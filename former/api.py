import os
from typing import Dict, Optional
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware


AIRFLOW_HOST = os.getenv("AIRFLOW_HOST", "http://localhost:9090")
AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL", f"{AIRFLOW_HOST}/api/v2")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "admin")
DEFAULT_DAG_ID = os.getenv("AIRFLOW_DAG_ID", "form_filler_pipeline")

app = FastAPI(
    title="Former Airflow Trigger API",
    description="Trigger the Airflow form filler DAG with a form URL.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)



class AirflowTriggerRequest(BaseModel):
    form_url: HttpUrl
    dag_id: Optional[str] = DEFAULT_DAG_ID
    run_id: Optional[str] = None


class AirflowTriggerResponse(BaseModel):
    dag_id: str
    dag_run_id: str
    state: str
    airflow_response: Dict
    
def get_airflow_access_token() -> str:
    token_url = f"{AIRFLOW_HOST}/auth/token"
    payload = {"username": AIRFLOW_USERNAME, "password": AIRFLOW_PASSWORD}

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(token_url, json=payload)
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise HTTPException(
                    status_code=502,
                    detail=f"Airflow token response missing access_token: {token_data}",
                )
            return access_token
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Airflow auth error: {exc.response.text}",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get Airflow access token: {exc}")

from datetime import datetime, timezone


def build_dag_run_payload(form_url: str, run_id: Optional[str] = None) -> Dict:
    payload = {"conf": {"form_url": form_url}}
    if run_id:
        payload["dag_run_id"] = run_id

    payload["logical_date"] = datetime.now(timezone.utc).isoformat()

    return payload


def trigger_airflow_dag(form_url: str, dag_id: str, run_id: Optional[str] = None) -> Dict:
    access_token = get_airflow_access_token()
    url = f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = build_dag_run_payload(form_url, run_id)

    try:
        with httpx.Client(headers=headers, timeout=30) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Airflow API error: {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to call Airflow API: {exc}")

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/airflow/trigger", response_model=AirflowTriggerResponse)
def airflow_trigger(request: AirflowTriggerRequest) -> AirflowTriggerResponse:
    payload = trigger_airflow_dag(str(request.form_url), request.dag_id, request.run_id)
    dag_run_id = payload.get("dag_run_id") or payload.get("dag_run", {}).get("dag_run_id", "")
    state = payload.get("state", "unknown")

    return AirflowTriggerResponse(
        dag_id=request.dag_id,
        dag_run_id=dag_run_id,
        state=state,
        airflow_response=payload,
    )
