import pytest
from datetime import datetime
from pydantic import ValidationError
from fastapi.testclient import TestClient

from former.backend.api import app
from former.backend.dagOperations import build_dag_run_payload
from former.backend.schemas import AirflowTriggerRequest


def test_health_check_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_airflow_trigger_request_validation():
    with pytest.raises(ValidationError):
        AirflowTriggerRequest(
            form_url="not-a-url",
            num_executions=0,
            base_interval_minutes=0.0,
            interval_jitter_minutes=-1.0,
        )


def test_build_dag_run_payload_default():
    payload = build_dag_run_payload("https://example.com/form")

    assert payload["conf"]["form_url"] == "https://example.com/form"
    assert payload["conf"]["num_executions"] == 1
    assert payload["conf"]["base_interval_minutes"] == 10.0
    assert payload["conf"]["interval_jitter_minutes"] == 2.0
    assert "logical_date" in payload
    assert "dag_run_id" not in payload

    datetime.fromisoformat(payload["logical_date"])


def test_build_dag_run_payload_with_run_id():
    payload = build_dag_run_payload(
        "https://example.com/form",
        run_id="test-run-id",
        num_executions=2,
        base_interval_minutes=5.0,
        interval_jitter_minutes=0.5,
    )

    assert payload["dag_run_id"] == "test-run-id"
    assert payload["conf"]["num_executions"] == 2
    assert payload["conf"]["base_interval_minutes"] == 5.0
    assert payload["conf"]["interval_jitter_minutes"] == 0.5
