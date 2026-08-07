"""Airflow run orchestration endpoints."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..airflowInterface.cancel_run import cancel_airflow_dag
from ..dispatch import dispatch_trigger
from ..db import get_db
from ..dependencies import get_current_user, get_verified_user
from ..models import (
    AirflowProgress,
    AirflowTriggerInternalRequest,
    FormRunAnswers,
    UserBillingInfo,
)
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
        state = (
            run.state
            if run.state in {"cancelled", "pending_dispatch", "dispatch_failed"}
            else get_progress_state(progress)
        )
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
    dag_run_id = build_run_id(payload.run_id, current_user["id"])
    interval_jitter_minutes = calculate_scheduler_jitter(
        payload.base_interval_minutes
    )
    expected_end_at = datetime.now(timezone.utc) + timedelta(
        minutes=payload.num_executions * payload.base_interval_minutes
    )

    # Reserve the full request while holding the billing row lock, and commit
    # the outbox record before making the cross-system Airflow call.
    try:
        billing = (
            db.query(UserBillingInfo)
            .filter_by(user_id=current_user["id"])
            .with_for_update()
            .first()
        )
        if not billing:
            raise HTTPException(status_code=404, detail="Billing information not found")
        if billing.form_fills_remaining < payload.num_executions:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Insufficient quota: requested {payload.num_executions}, "
                    f"available {billing.form_fills_remaining}"
                ),
            )

        trigger = AirflowTriggerInternalRequest(
            user_id=current_user["id"],
            user_email=current_user["email"],
            form_url=str(payload.form_url),
            dag_id=payload.dag_id,
            run_id=dag_run_id,
            run_name=payload.run_name,
            num_executions=payload.num_executions,
            base_interval_minutes=payload.base_interval_minutes,
            interval_jitter_minutes=interval_jitter_minutes,
            expected_end_at=expected_end_at,
            quota_reserved=payload.num_executions,
            age_profile=(payload.conf_personality or {}).get("age_profile"),
            political_leaning=(payload.conf_personality or {}).get("political_leaning"),
            risk_tolerance=(payload.conf_personality or {}).get("risk_tolerance"),
            verbosity=(payload.conf_personality or {}).get("verbosity"),
            formality=(payload.conf_personality or {}).get("formality"),
        )
        billing.form_fills_remaining -= payload.num_executions
        db.add(trigger)
        db.commit()
        db.refresh(trigger)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reserve form-fill quota") from exc

    try:
        response_payload = dispatch_trigger(db, trigger)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Run reserved as {dag_run_id}; Airflow dispatch will be retried",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Run reserved as {dag_run_id}; Airflow dispatch will be retried",
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

    if run.state == "cancelled":
        return {"dag_run_id": dag_run_id, "state": "cancelled", "message": "Run was already cancelled"}
    if run.state == "dispatching":
        raise HTTPException(
            status_code=409,
            detail="Run dispatch is in progress; retry cancellation shortly",
        )

    try:
        if run.state in {"pending_dispatch", "dispatch_failed"}:
            response = {"state": "not_dispatched"}
        else:
            response = await cancel_airflow_dag(
                run.dag_id,
                dag_run_id,
                cancel_children=True,
            )
        run = db.query(AirflowTriggerInternalRequest).filter_by(
            id=run.id
        ).with_for_update().one()
        if run.state == "cancelled":
            return {
                "dag_run_id": dag_run_id,
                "state": "cancelled",
                "message": "Run was already cancelled",
                "airflow_response": response,
            }
        outstanding = run.quota_reserved - run.quota_settled - run.quota_refunded
        completed_indexes = {
            row.execution_index
            for row in db.query(FormRunAnswers).filter_by(run_id=run.run_id).all()
        }
        for execution_index in range(run.num_executions):
            if execution_index not in completed_indexes:
                db.add(FormRunAnswers(
                    run_id=run.run_id,
                    execution_index=execution_index,
                    form_url=run.form_url,
                    answers=[],
                    questions=[],
                    success=False,
                    error_message="Cancelled before terminal child outcome",
                ))
        progress = db.query(AirflowProgress).filter_by(
            run_id=run.run_id
        ).with_for_update().first()
        if progress:
            progress.hasFailedRuns = True
        else:
            db.add(AirflowProgress(
                run_id=run.run_id,
                numberOfSuccessfulRuns=run.quota_settled,
                hasFailedRuns=True,
                expectedTotalRuns=run.num_executions,
            ))
        if outstanding > 0:
            billing = (
                db.query(UserBillingInfo)
                .filter_by(user_id=run.user_id)
                .with_for_update()
                .first()
            )
            if billing:
                billing.form_fills_remaining += outstanding
                run.quota_refunded += outstanding
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
