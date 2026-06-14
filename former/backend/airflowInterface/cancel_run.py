import asyncio
from typing import Dict
import httpx

from former.backend.airflowInterface.airflow_utils import get_child_dag_runs
from former.backend.airflowInterface.airflow_utils import get_airflow_access_token
from former.config import AIRFLOW_BASE_URL




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