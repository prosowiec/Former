from datetime import datetime, timezone
from typing import Dict, Optional
import json
import httpx
from azure.identity import ClientSecretCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from former.backend.airflowInterface.airflow_utils import get_airflow_access_token

from former.config import (
    AIRFLOW_BASE_URL,
    AIRFLOW_MODE,
    AZURE_SUBSCRIPTION_ID,
    AZURE_RESOURCE_GROUP,
    AZURE_CLIENT_ID,
    AZURE_CLIENT_SECRET,
    AZURE_TENANT_ID,
    ACI_IMAGE
)



def build_dag_run_payload(
    form_url: str,
    user_id : str,
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
            "user_id" : user_id,
        }
    }
    if run_id:
        payload["dag_run_id"] = run_id

    payload["logical_date"] = (logical_date or datetime.now(timezone.utc)).isoformat()
    return payload

def trigger_airflow_local(
    form_url: str,
    dag_id: str,
    user_id: str,
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
        form_url, user_id, run_id, num_executions, base_interval_minutes, interval_jitter_minutes, logical_date
    )

    with httpx.Client(headers=headers, timeout=30) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    
def trigger_airflow_aci(
    form_url: str,
    dag_id: str,
    user_id: str,
    run_id: Optional[str] = None,
    num_executions: int = 1,
    base_interval_minutes: float = 10.0,
    interval_jitter_minutes: float = 2.0,
    logical_date: Optional[datetime] = None,
) -> Dict:

    credential = ClientSecretCredential(
        tenant_id=AZURE_TENANT_ID,
        client_id=AZURE_CLIENT_ID,
        client_secret=AZURE_CLIENT_SECRET,
    )

    client = ContainerInstanceManagementClient(
        credential,
        AZURE_SUBSCRIPTION_ID,
    )

    container_group_name = f"airflow-trigger-{user_id}-{int(datetime.utcnow().timestamp())}"

    payload = build_dag_run_payload(
        form_url=form_url,
        user_id=user_id,
        run_id=run_id,
        num_executions=num_executions,
        base_interval_minutes=base_interval_minutes,
        interval_jitter_minutes=interval_jitter_minutes,
        logical_date=logical_date,
    )

    command = [
        "python",
        "/app/trigger_dag.py",
        "--dag-id",
        dag_id,
        "--payload",
        json.dumps(payload),
    ]

    container_group = {
        "location": "westeurope",
        "containers": [
            {
                "name": "airflow-trigger",
                "image": ACI_IMAGE,
                "command": command,
                "resources": {
                    "requests": {
                        "cpu": 1,
                        "memory_in_gb": 2,
                    }
                },
            }
        ],
        "os_type": "Linux",
        "restart_policy": "Never",
    }

    client.container_groups.begin_create_or_update(
        AZURE_RESOURCE_GROUP,
        container_group_name,
        container_group,
    ).result()

    return {
        "status": "submitted",
        "container_group": container_group_name,
    }


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

    if AIRFLOW_MODE == "PROD":
        return trigger_airflow_aci(
            form_url=form_url,
            dag_id=dag_id,
            user_id=user_id,
            run_id=run_id,
            num_executions=num_executions,
            base_interval_minutes=base_interval_minutes,
            interval_jitter_minutes=interval_jitter_minutes,
            logical_date=logical_date,
        )

    return trigger_airflow_local(
        form_url=form_url,
        dag_id=dag_id,
        user_id=user_id,
        run_id=run_id,
        num_executions=num_executions,
        base_interval_minutes=base_interval_minutes,
        interval_jitter_minutes=interval_jitter_minutes,
        logical_date=logical_date,
    )


