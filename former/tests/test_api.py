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
