from datetime import datetime, timezone
from typing import Dict, Optional

import httpx

from former.config import AIRFLOW_HOST, AIRFLOW_PASSWORD, AIRFLOW_USERNAME, AIRFLOW_BASE_URL


def get_airflow_access_token() -> str:
    token_url = f"{AIRFLOW_HOST}/auth/token"
    payload = {"username": AIRFLOW_USERNAME, "password": AIRFLOW_PASSWORD}

    with httpx.Client(timeout=30) as client:
        response = client.post(token_url, json=payload)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data.get("access_token")
        return access_token



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
        form_url,
        run_id,
        num_executions,
        base_interval_minutes,
        interval_jitter_minutes,
        logical_date,
    )

    with httpx.Client(headers=headers, timeout=30) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()


def get_child_dag_runs(parent_run_id: str) -> list:
    """Get all child DAG runs triggered by a parent DAG run."""
    access_token = get_airflow_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Query for child DAGs that match the parent run pattern
    # Child run IDs follow pattern: {parent_run_id}__item_{i}
    child_runs = []
    
    try:
        # Get all form_filler_dag runs that match the parent pattern
        url = f"{AIRFLOW_BASE_URL}/dags/form_filler_dag/dagRuns"
        with httpx.Client(headers=headers, timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Filter for child runs matching this parent
            for run in data.get("dag_runs", []):
                if run["dag_run_id"].startswith(f"{parent_run_id}__item_"):
                    child_runs.append(run)
    except Exception as e:
        print(f"Warning: Could not fetch child DAG runs: {e}")
    
    return child_runs


def cancel_airflow_dag(dag_id: str, run_id: str, cancel_children: bool = True) -> Dict:
    """Cancel an Airflow DAG run by setting its state to failed.
    
    If cancel_children is True and this is a parent DAG, also cancel all child DAG runs.
    """
    access_token = get_airflow_access_token()
    url = f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns/{run_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"state": "failed"}
    
    response_data = {}

    # If this is a parent DAG (form_filler_plan), cancel all child DAGs
    if cancel_children and dag_id == "form_filler_plan":
        print(f"Cancelling child DAG runs for parent run: {run_id}")
        child_runs = get_child_dag_runs(run_id)
        response_data["cancelled_children"] = []
        
        for child_run in child_runs:
            try:
                child_dag_id = child_run["dag_id"]
                child_run_id = child_run["dag_run_id"]
                print(f"  Cancelling child DAG: {child_dag_id}/{child_run_id}")
                
                child_url = f"{AIRFLOW_BASE_URL}/dags/{child_dag_id}/dagRuns/{child_run_id}"
                with httpx.Client(headers=headers, timeout=30) as client:
                    client.patch(child_url, json=payload)
                
                response_data["cancelled_children"].append({
                    "dag_id": child_dag_id,
                    "run_id": child_run_id,
                    "status": "cancelled"
                })
            except Exception as e:
                print(f"  Error cancelling child DAG run {child_run['dag_run_id']}: {e}")
                response_data["cancelled_children"].append({
                    "dag_id": child_run["dag_id"],
                    "run_id": child_run["dag_run_id"],
                    "status": "error",
                    "error": str(e)
                })
    
    # Cancel the parent DAG
    with httpx.Client(headers=headers, timeout=30) as client:
        response = client.patch(url, json=payload)
        response.raise_for_status()
        response_data["parent"] = response.json()
    
    return response_data
