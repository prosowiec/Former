import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx
from sqlalchemy import create_engine, text

from former.config import (
    AIRFLOW_HOST, 
    AIRFLOW_PASSWORD, 
    AIRFLOW_USERNAME, 
    AIRFLOW_BASE_URL,
    AIRFLOW_DB_URI
)

db_engine = create_engine(AIRFLOW_DB_URI)

def get_airflow_access_token() -> str:
    token_url = f"{AIRFLOW_HOST}/auth/token"
    payload = {"username": AIRFLOW_USERNAME, "password": AIRFLOW_PASSWORD}

    with httpx.Client(timeout=30) as client:
        response = client.post(token_url, json=payload)
        response.raise_for_status()
        token_data = response.json()
        return token_data.get("access_token")

def build_dag_run_payload(
    form_url: str,
    run_id: Optional[str] = None,
    num_executions: int = 1,
    base_interval_minutes: float = 10.0,
    interval_jitter_minutes: float = 2.0,
    logical_date: Optional[datetime] = None,
) -> Dict:
    payload = {
        "conf": {
            "form_url": form_url,
            "num_executions": num_executions,
            "base_interval_minutes": base_interval_minutes,
            "interval_jitter_minutes": interval_jitter_minutes,
        }
    }
    if run_id:
        payload["dag_run_id"] = run_id

    payload["logical_date"] = (logical_date or datetime.now(timezone.utc)).isoformat()
    return payload

def trigger_airflow_dag(
    form_url: str,
    dag_id: str,
    run_id: Optional[str] = None,
    num_executions: int = 1,
    base_interval_minutes: float = 10.0,
    interval_jitter_minutes: float = 2.0,
    logical_date: Optional[datetime] = None,
) -> Dict:
    access_token = get_airflow_access_token()
    url = f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = build_dag_run_payload(
        form_url, run_id, num_executions, base_interval_minutes, interval_jitter_minutes, logical_date
    )

    with httpx.Client(headers=headers, timeout=30) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def _fetch_child_runs_from_db(parent_run_id: str) -> list:
    """Synchronous helper to execute the SQL query."""
    child_runs = []
    
    query = text("""
        SELECT dag_id, run_id, state 
        FROM dag_run 
        WHERE dag_id = 'form_filler_dag' 
          AND run_id LIKE :pattern
    """)
    
    try:
        with db_engine.connect() as conn:
            result = conn.execute(query, {"pattern": f"{parent_run_id}__item_%"})
            
            for row in result:
                child_runs.append({
                    "dag_run_id": row.run_id,
                    "state": row.state
                })
    except Exception as e:
        print(f"Warning: Could not fetch child DAG runs from DB: {e}")
        
    return child_runs


async def get_child_dag_runs(parent_run_id: str, client) -> list:
    """Get all child DAG runs by querying the Airflow database directly."""    
    # We use asyncio.to_thread to prevent the synchronous SQLAlchemy 
    # connection from blocking your async HTTP operations
    return await asyncio.to_thread(_fetch_child_runs_from_db, parent_run_id)


async def cancel_child(child_run, client, payload):
    try:
        child_dag_id = "form_filler_dag"
        child_run_id = child_run.get("dag_run_id")

        if not child_run_id:
            print(f"Warning: Could not find dag_run_id in child run: {child_run}")
            return None

        child_url = f"{AIRFLOW_BASE_URL}/dags/{child_dag_id}/dagRuns/{child_run_id}"
        print(f"Cancelling child DAG: {child_dag_id}/{child_run_id}")

        response = await client.patch(child_url, json=payload)
        response.raise_for_status()

        print(f"Successfully cancelled: {child_run_id}")
        return {
            "dag_id": child_dag_id,
            "run_id": child_run_id,
            "status": "cancelled",
        }

    except Exception as e:
        print(f"Error cancelling child DAG run: {e}")
        return {
            "dag_id": "form_filler_dag",
            "run_id": child_run.get("dag_run_id", "unknown"),
            "status": "error",
            "error": str(e),
        }
                    
async def cancel_airflow_dag(dag_id: str, run_id: str, cancel_children: bool = True) -> Dict:
    """
    Cancel an Airflow DAG run by setting its state to failed.
    If cancel_children is True and this is a parent DAG, also cancel all child DAG runs.
    """
    access_token = get_airflow_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"state": "failed"}

    response_data = {}

    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        parent_url = f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns/{run_id}"

        response = await client.patch(parent_url, json=payload)
        response.raise_for_status()

        if cancel_children and dag_id == "form_filler_plan":
            print(f"Cancelling child DAG runs for parent run: {run_id}")

            child_runs = await get_child_dag_runs(run_id, client)
            response_data["cancelled_children"] = []
            print(f"Found {len(child_runs)} child runs to cancel.")
            
            results = await asyncio.gather(
                *(cancel_child(child_run, client, payload) for child_run in child_runs),
                return_exceptions=False,
            )

            response_data["cancelled_children"] = [
                r for r in results if r is not None
            ]


        response_data["parent"] = response.json()

    return response_data