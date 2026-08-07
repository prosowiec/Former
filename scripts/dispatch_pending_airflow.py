"""Retry persisted Airflow outbox records."""

import argparse
import time

from former.backend.db import SessionLocal
from former.backend.dispatch import dispatch_trigger
from former.backend.models import AirflowTriggerInternalRequest


def dispatch_once() -> None:
    db = SessionLocal()
    try:
        pending = db.query(AirflowTriggerInternalRequest).filter(
            AirflowTriggerInternalRequest.state.in_(("pending_dispatch", "dispatching", "dispatch_failed"))
        ).all()
        for trigger in pending:
            try:
                dispatch_trigger(db, trigger)
            except Exception as exc:
                print(f"Dispatch retry failed for {trigger.run_id}: {exc}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval", type=float, default=30.0)
    args = parser.parse_args()
    while True:
        dispatch_once()
        if not args.loop:
            break
        time.sleep(max(1.0, args.interval))


if __name__ == "__main__":
    main()
