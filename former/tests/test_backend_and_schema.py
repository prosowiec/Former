from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from former.backend.api import app
from former.backend.airflowInterface.trigger_run import build_dag_run_payload
from former.backend.schemas import AirflowTriggerRequest


def test_health_check_endpoint():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_airflow_trigger_request_validation():
    with pytest.raises(ValidationError):
        AirflowTriggerRequest(form_url="https://example.com/form")


def test_build_dag_run_payload():
    payload = build_dag_run_payload(
        "https://docs.google.com/forms/d/e/example/viewform",
        user_id="user-1",
        run_id="run-1",
        num_executions=2,
        base_interval_minutes=5.0,
        interval_jitter_minutes=0.5,
    )
    assert payload["dag_run_id"] == "run-1"
    assert payload["conf"]["user_id"] == "user-1"
    assert payload["conf"]["num_executions"] == 2
    datetime.fromisoformat(payload["logical_date"])
