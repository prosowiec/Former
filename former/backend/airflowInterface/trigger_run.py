from datetime import datetime, timezone
from typing import Dict, Optional
from urllib.parse import quote

import httpx

from former.backend.airflowInterface.airflow_utils import get_airflow_access_token
from former.config import AIRFLOW_BASE_URL


def build_dag_run_payload(
    form_url: str,
    user_id: str,
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
            "user_id": user_id,
        },
        "logical_date": (logical_date or datetime.now(timezone.utc)).isoformat(),
    }
    if run_id:
        payload["dag_run_id"] = run_id
    return payload


def trigger_airflow_dag(
    form_url: str,
    dag_id: str,
    user_id: str,
    run_id: Optional[str] = None,
    num_executions: int = 1,
    base_interval_minutes: float = 10.0,
    interval_jitter_minutes: float = 2.0,
    logical_date: Optional[datetime] = None,
) -> Dict:
    """Trigger a DAG on the continuously running Airflow API."""
    access_token = get_airflow_access_token()
    encoded_dag_id = quote(dag_id, safe="")
    url = f"{AIRFLOW_BASE_URL.rstrip('/')}/dags/{encoded_dag_id}/dagRuns"
    payload = build_dag_run_payload(
        form_url=form_url,
        user_id=user_id,
        run_id=run_id,
        num_executions=num_executions,
        base_interval_minutes=base_interval_minutes,
        interval_jitter_minutes=interval_jitter_minutes,
        logical_date=logical_date,
    )

    with httpx.Client(
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    ) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
