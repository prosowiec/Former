from fastapi.testclient import TestClient

from former.backend.api import app


def test_airflow_trigger_endpoint(monkeypatch):
    def fake_trigger(
        form_url,
        dag_id,
        run_id=None,
        num_executions=1,
        base_interval_minutes=10.0,
        interval_jitter_minutes=2.0,
    ):
        assert form_url == "https://example.com/form"
        assert dag_id == "form_filler_pipeline"
        assert run_id is None
        assert num_executions == 1
        assert base_interval_minutes == 10.0
        assert interval_jitter_minutes == 2.0
        return {"dag_run_id": "test-run-id", "state": "queued"}

    monkeypatch.setattr("former.backend.api.trigger_airflow_dag", fake_trigger)
    monkeypatch.setattr("former.backend.api.get_current_user", lambda request: {"email": "test@example.com"})
    client = TestClient(app)

    response = client.post(
        "/airflow/trigger",
        json={"form_url": "https://example.com/form", "dag_id": "form_filler_pipeline"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dag_id"] == "form_filler_pipeline"
    assert payload["dag_run_id"] == "test-run-id"
    assert payload["state"] == "queued"
    assert payload["airflow_response"]["dag_run_id"] == "test-run-id"
    assert payload["num_executions"] == 1


def test_airflow_trigger_endpoint_multiple_runs(monkeypatch):
    called = []

    def fake_trigger(
        form_url,
        dag_id,
        run_id=None,
        num_executions=1,
        base_interval_minutes=10.0,
        interval_jitter_minutes=2.0,
    ):
        called.append((form_url, dag_id, run_id, num_executions, base_interval_minutes, interval_jitter_minutes))
        return {"dag_run_id": "test-run-id", "state": "queued"}

    monkeypatch.setattr("former.backend.api.trigger_airflow_dag", fake_trigger)
    monkeypatch.setattr("former.backend.api.get_current_user", lambda request: {"email": "test@example.com"})
    client = TestClient(app)

    response = client.post(
        "/airflow/trigger",
        json={
            "form_url": "https://example.com/form",
            "dag_id": "form_filler_pipeline",
            "num_executions": 3,
            "base_interval_minutes": 10,
            "interval_jitter_minutes": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dag_id"] == "form_filler_pipeline"
    assert payload["num_executions"] == 3
    assert payload["base_interval_minutes"] == 10
    assert payload["interval_jitter_minutes"] == 1
    assert payload["dag_run_id"] == "test-run-id"
    assert payload["state"] == "queued"
    assert len(called) == 1
    assert called[0][3] == 3
    assert called[0][4] == 10
    assert called[0][5] == 1


def test_list_airflow_runs_endpoint(monkeypatch):
    from types import SimpleNamespace
    from datetime import datetime

    runs = [
        SimpleNamespace(
            user_email="test@example.com",
            form_url="https://example.com/form",
            dag_id="form_filler_pipeline",
            run_id="test-run-id",
            num_executions=3,
            base_interval_minutes=10.0,
            interval_jitter_minutes=1.0,
            created_at=datetime(2026, 1, 1, 12, 0, 0),
        )
    ]
    progresses = [
        SimpleNamespace(
            dag_id="test-run-id",
            numberOfSuccessfulRuns=1,
            hasFailedRuns=False,
            expectedTotalRuns=3,
        )
    ]

    class DummyQuery:
        def __init__(self, items):
            self._items = items
        def filter_by(self, **kwargs):
            return self
        def order_by(self, *args):
            return self
        def all(self):
            return self._items
        def filter(self, *args):
            return self

    class DummySession:
        def query(self, model):
            if model.__name__ == "AirflowTriggerInternalRequest":
                return DummyQuery(runs)
            if model.__name__ == "AirflowProgress":
                return DummyQuery(progresses)
            raise AssertionError(f"Unexpected model queried: {model}")

    def fake_get_db():
        yield DummySession()

    monkeypatch.setattr("former.backend.api.get_current_user", lambda request: {"email": "test@example.com"})
    monkeypatch.setattr("former.backend.api", "get_db", fake_get_db)

    client = TestClient(app)
    response = client.get("/airflow/runs")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["dag_run_id"] == "test-run-id"
    assert payload[0]["state"] == "running"
    assert payload[0]["progress"]["numberOfSuccessfulRuns"] == 1
