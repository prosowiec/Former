from datetime import datetime, timezone

from former.backend.airflowInterface import trigger_run


def test_build_dag_run_payload():
    payload = trigger_run.build_dag_run_payload(
        form_url="https://example.com/form",
        user_id="user-123",
        run_id="run-123",
        num_executions=2,
        base_interval_minutes=5,
        interval_jitter_minutes=1,
        logical_date=datetime(2026, 7, 21, 20, 0, tzinfo=timezone.utc),
    )

    assert payload == {
        "conf": {
            "form_url": "https://example.com/form",
            "num_executions": 2,
            "base_interval_minutes": 5,
            "interval_jitter_minutes": 1,
            "user_id": "user-123",
        },
        "dag_run_id": "run-123",
        "logical_date": "2026-07-21T20:00:00+00:00",
    }


def test_trigger_calls_always_running_airflow_api(monkeypatch):
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "dag_id": "form/filler",
                "dag_run_id": "run-123",
                "state": "queued",
            }

    class FakeHttpClient:
        def __init__(self, headers, timeout):
            assert headers == {"Authorization": "Bearer airflow-token"}
            assert timeout == 30

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def post(self, url, json):
            calls.append((url, json))
            return FakeResponse()

    monkeypatch.setattr(trigger_run, "AIRFLOW_BASE_URL", "http://localhost:8080/api/v2")
    monkeypatch.setattr(trigger_run, "get_airflow_access_token", lambda: "airflow-token")
    monkeypatch.setattr(trigger_run.httpx, "Client", FakeHttpClient)

    result = trigger_run.trigger_airflow_dag(
        form_url="https://example.com/form",
        dag_id="form/filler",
        user_id="user-123",
        run_id="run-123",
    )

    assert calls[0][0] == "http://localhost:8080/api/v2/dags/form%2Ffiller/dagRuns"
    assert calls[0][1]["dag_run_id"] == "run-123"
    assert result["state"] == "queued"
