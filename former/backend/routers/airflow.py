"""Airflow run orchestration endpoints."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..airflowInterface.cancel_run import cancel_airflow_dag
from ..airflowInterface.trigger_run import trigger_airflow_dag
from ..db import get_db
from ..dependencies import get_current_user, get_verified_user
from ..models import AirflowProgress, AirflowTriggerInternalRequest
from ..schemas import AirflowRunResponse, AirflowTriggerRequest, AirflowTriggerResponse
from ...config import SCHEDULER_JITTER_RATIO, SCHEDULER_MAX_JITTER_MINUTES


router = APIRouter(prefix="/airflow", tags=["airflow"])


def get_progress_state(progress: AirflowProgress | None) -> str:
    if not progress:
        return "queued"
    if progress.hasFailedRuns:
        return "failed"
    if progress.numberOfSuccessfulRuns >= progress.expectedTotalRuns:
        return "success"
    if progress.numberOfSuccessfulRuns > 0:
        return "running"
    return "queued"


def build_run_id(
    base_run_id: Optional[str],
    user_id: str,
    max_length: int = 255,
) -> str:
    candidate = (
        f"{base_run_id}_{user_id}"
        if base_run_id
        else f"former_run_{secrets.token_hex(8)}"
    )
    if len(candidate) <= max_length:
        return candidate

    digest = hashlib.sha1(candidate.encode("utf-8")).hexdigest()[:16]
    prefix_length = max_length - len(digest) - 1
    return f"{candidate[:prefix_length]}_{digest}"


def calculate_scheduler_jitter(base_interval_minutes: float) -> float:
    return round(
        min(
            SCHEDULER_MAX_JITTER_MINUTES,
            base_interval_minutes * SCHEDULER_JITTER_RATIO,
        ),
        4,
    )


def to_utc_iso(value: datetime | None) -> str:
    timestamp = value or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@router.get("/runs", response_model=list[AirflowRunResponse])
def list_airflow_runs(
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    runs = (
        db.query(AirflowTriggerInternalRequest)
        .filter_by(user_email=current_user["email"])
        .order_by(AirflowTriggerInternalRequest.created_at.desc())
        .all()
    )

    run_ids = [run.run_id for run in runs]
    progress_by_run = {}
    if run_ids:
        progress_rows = (
            db.query(AirflowProgress)
            .filter(AirflowProgress.run_id.in_(run_ids))
            .all()
        )
        progress_by_run = {row.run_id: row for row in progress_rows}

    result = []
    for run in runs:
        progress = progress_by_run.get(run.run_id)
        state = run.state if run.state == "cancelled" else get_progress_state(progress)
        result.append(
            {
                "dag_id": run.dag_id,
                "dag_run_id": run.run_id,
                "form_url": run.form_url,
                "num_executions": run.num_executions,
                "base_interval_minutes": run.base_interval_minutes,
                "interval_jitter_minutes": run.interval_jitter_minutes,
                "created_at": to_utc_iso(run.created_at),
                "expected_end_at": to_utc_iso(run.expected_end_at),
                "state": state,
                "run_name": run.run_name,
                "age_profile": run.age_profile,
                "political_leaning": run.political_leaning,
                "risk_tolerance": run.risk_tolerance,
                "verbosity": run.verbosity,
                "formality": run.formality,
                "progress": (
                    {
                        "numberOfSuccessfulRuns": progress.numberOfSuccessfulRuns,
                        "hasFailedRuns": progress.hasFailedRuns,
                        "expectedTotalRuns": progress.expectedTotalRuns,
                    }
                    if progress
                    else None
                ),
            }
        )
    return result


@router.post("/trigger", response_model=AirflowTriggerResponse)
def airflow_trigger(
    payload: AirflowTriggerRequest,
    current_user: Annotated[Dict, Depends(get_verified_user)],
    db: Session = Depends(get_db),
) -> AirflowTriggerResponse:
    try:
        dag_run_id = build_run_id(payload.run_id, current_user["id"])
        interval_jitter_minutes = calculate_scheduler_jitter(
            payload.base_interval_minutes
        )
        expected_end_at = datetime.now(timezone.utc) + timedelta(
            minutes=payload.num_executions * payload.base_interval_minutes
        )
        response_payload = trigger_airflow_dag(
            str(payload.form_url),
            payload.dag_id,
            current_user["id"],
            dag_run_id,
            payload.num_executions,
            payload.base_interval_minutes,
            interval_jitter_minutes,
        )

        db.add(
            AirflowTriggerInternalRequest(
                user_email=current_user["email"],
                form_url=str(payload.form_url),
                dag_id=payload.dag_id,
                run_id=dag_run_id,
                run_name=payload.run_name,
                num_executions=payload.num_executions,
                base_interval_minutes=payload.base_interval_minutes,
                interval_jitter_minutes=interval_jitter_minutes,
                expected_end_at=expected_end_at,
                age_profile=(
                    payload.conf_personality.get("age_profile")
                    if payload.conf_personality
                    else None
                ),
                political_leaning=(
                    payload.conf_personality.get("political_leaning")
                    if payload.conf_personality
                    else None
                ),
                risk_tolerance=(
                    payload.conf_personality.get("risk_tolerance")
                    if payload.conf_personality
                    else None
                ),
                verbosity=(
                    payload.conf_personality.get("verbosity")
                    if payload.conf_personality
                    else None
                ),
                formality=(
                    payload.conf_personality.get("formality")
                    if payload.conf_personality
                    else None
                ),
            )
        )
        db.commit()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Airflow API error: {exc.response.text}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to call Airflow API: {exc}",
        ) from exc

    dag_run_id = (
        response_payload.get("dag_run_id")
        or response_payload.get("dag_run", {}).get("dag_run_id")
        or dag_run_id
    )
    return AirflowTriggerResponse(
        dag_id=payload.dag_id,
        dag_run_id=dag_run_id,
        state=response_payload.get("state", "queued"),
        num_executions=payload.num_executions,
        base_interval_minutes=payload.base_interval_minutes,
        interval_jitter_minutes=interval_jitter_minutes,
        expected_end_at=to_utc_iso(expected_end_at),
        airflow_response=response_payload,
    )


@router.post("/runs/{dag_run_id}/cancel")
async def cancel_airflow_run(
    dag_run_id: str,
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    run = (
        db.query(AirflowTriggerInternalRequest)
        .filter_by(run_id=dag_run_id, user_email=current_user["email"])
        .first()
    )
    if not run:
        raise HTTPException(
            status_code=404,
            detail="Run not found or you don't have permission to cancel it",
        )

    try:
        response = await cancel_airflow_dag(
            run.dag_id,
            dag_run_id,
            cancel_children=True,
        )
        run.state = "cancelled"
        db.commit()
        return {
            "dag_run_id": dag_run_id,
            "state": "cancelled",
            "message": "Run cancelled successfully",
            "airflow_response": response,
        }
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Airflow API error: {exc.response.text}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel run: {exc}",
        ) from exc
