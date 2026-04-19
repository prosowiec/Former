import json
from pathlib import Path

from fastapi.testclient import TestClient

from former.backend.api import app
from former.backend import auth
from former.backend.users import AUTH_USERS_FILE, hash_password


def test_auth_me_returns_unauthenticated_by_default():
    client = TestClient(app)

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {"user": None}


def test_build_google_login_url_uses_state_and_redirect():
    auth.GOOGLE_CLIENT_ID = "test-client-id"
    auth.GOOGLE_CLIENT_SECRET = "test-client-secret"
    auth.GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:8000/auth/callback"

    url = auth.build_google_login_url("test-state")

    assert "client_id=test-client-id" in url
    assert "state=test-state" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fauth%2Fcallback" in url


def test_standard_login_sets_session(monkeypatch, tmp_path):
    auth_file = tmp_path / "auth_users.json"
    monkeypatch.setattr("former.backend.users.AUTH_USERS_FILE", str(auth_file))

    users = {
        "tester@example.com": {
            "email": "tester@example.com",
            "password_hash": hash_password("password123"),
            "name": "Test",
            "surname": "User",
        }
    }
    auth_file.write_text(json.dumps(users), encoding="utf-8")

    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"email": "tester@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Logged in"

    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "tester"


def test_airflow_trigger_requires_authentication():
    client = TestClient(app)
    response = client.post(
        "/airflow/trigger",
        json={
            "form_url": "https://example.com/form",
            "dag_id": "form_filler_pipeline",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"
