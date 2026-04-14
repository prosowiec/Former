from fastapi.testclient import TestClient

from former.backend.api import app


def test_airflow_trigger_endpoint(monkeypatch):
    def fake_trigger(form_url, dag_id, run_id=None):
        assert form_url == "https://example.com/form"
        assert dag_id == "form_filler_pipeline"
        assert run_id is None
        return {"dag_run_id": "test-run-id", "state": "queued"}

    monkeypatch.setattr("former.api.trigger_airflow_dag", fake_trigger)
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
