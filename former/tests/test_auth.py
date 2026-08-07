from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from former.backend.api import app
from former.backend.db import Base, get_db


def _client_with_database():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), engine


def test_auth_me_requires_authentication():
    client, engine = _client_with_database()
    try:
        assert client.get("/auth/me").status_code == 401
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_registration_sends_verification_and_uses_httponly_cookies(monkeypatch):
    client, engine = _client_with_database()
    sent_to = []
    monkeypatch.setattr(
        "former.backend.routers.auth.send_email_verification",
        lambda email, _db: sent_to.append(email),
    )
    try:
        registered = client.post(
            "/auth/register",
            json={
                "email": "tester@example.com",
                "password": "password123",
                "name": "Test",
                "surname": "User",
            },
        )
        assert registered.status_code == 200
        assert "access_token" not in registered.json()
        cookies = registered.headers.get_list("set-cookie")
        assert any("access_token=" in value and "HttpOnly" in value for value in cookies)
        assert any("refresh_token=" in value and "HttpOnly" in value for value in cookies)
        assert sent_to == ["tester@example.com"]

        me = client.get("/auth/me")
        assert me.status_code == 200
        assert me.json()["user"]["email"] == "tester@example.com"
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
