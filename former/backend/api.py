from typing import Dict, Optional
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .dagOperations import trigger_airflow_dag
from .schemas import AirflowTriggerRequest, AirflowTriggerResponse

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


    

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/airflow/trigger", response_model=AirflowTriggerResponse)
def airflow_trigger(request: AirflowTriggerRequest) -> AirflowTriggerResponse:
    try:
        payload = trigger_airflow_dag(
            str(request.form_url),
            request.dag_id,
            request.run_id,
            request.num_executions,
            request.base_interval_minutes,
            request.interval_jitter_minutes,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Airflow API error: {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to call Airflow API: {exc}")

    dag_run_id = payload.get("dag_run_id") or payload.get("dag_run", {}).get("dag_run_id", "")
    state = payload.get("state", "unknown")

    return AirflowTriggerResponse(
        dag_id=request.dag_id,
        dag_run_id=dag_run_id,
        state=state,
        num_executions=request.num_executions,
        base_interval_minutes=request.base_interval_minutes,
        interval_jitter_minutes=request.interval_jitter_minutes,
        airflow_response=payload,
    )
