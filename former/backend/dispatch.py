"""Durable dispatch helpers for the Airflow trigger outbox."""

from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from .airflowInterface.trigger_run import trigger_airflow_dag
from .models import AirflowTriggerInternalRequest


def dispatch_trigger(db: Session, trigger: AirflowTriggerInternalRequest) -> dict:
    """Dispatch a persisted trigger using its stable run id.

    Airflow treats ``dag_run_id`` as an idempotency key. A retry that receives an
    already-exists response is reconciled separately by the operator rather than
    creating a second logical run.
    """
    trigger = db.query(AirflowTriggerInternalRequest).filter_by(
        id=trigger.id
    ).with_for_update().one()
    if trigger.state == "cancelled":
        return {"dag_run_id": trigger.run_id, "state": "cancelled"}
    trigger.state = "dispatching"
    trigger.dispatch_attempts += 1
    db.commit()
    try:
        result = trigger_airflow_dag(
            trigger.form_url,
            trigger.dag_id,
            trigger.user_id,
            trigger.run_id,
            trigger.num_executions,
            trigger.base_interval_minutes,
            trigger.interval_jitter_minutes,
        )
    except httpx.HTTPStatusError as exc:
        # A stable dag_run_id makes a 409 the expected result when Airflow
        # accepted an earlier attempt but the response was lost.
        if exc.response.status_code == 409:
            result = {"dag_run_id": trigger.run_id, "state": "queued", "reconciled": True}
        else:
            trigger.state = "dispatch_failed"
            trigger.last_dispatch_error = str(exc)[:4000]
            db.commit()
            raise
    except Exception as exc:
        trigger.state = "dispatch_failed"
        trigger.last_dispatch_error = str(exc)[:4000]
        db.commit()
        raise

    trigger.state = "active"
    trigger.last_dispatch_error = None
    trigger.dispatched_at = datetime.now(timezone.utc)
    db.commit()
    return result
