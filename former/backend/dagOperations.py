from datetime import datetime, timezone
from typing import Dict, Optional

import httpx

from former.backend.config import AIRFLOW_HOST, AIRFLOW_PASSWORD, AIRFLOW_USERNAME, AIRFLOW_BASE_URL


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
