from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from former.backend.api import app
from former.backend.db import Base, get_db
from former.backend.models import User


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
        assert me.json()["user"]["has_password"] is True
        assert me.json()["user"]["has_google_login"] is False
        assert me.json()["user"]["created_at"] is not None
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_change_email_requires_password_and_ends_session(monkeypatch):
    client, engine = _client_with_database()
    monkeypatch.setattr(
        "former.backend.routers.auth.send_email_verification",
        lambda _email, _db: None,
    )
    verification_sent = []
    monkeypatch.setattr(
        "former.backend.users.send_email_verification",
        lambda email, _db: verification_sent.append(email),
    )
    try:
        registered = client.post(
            "/auth/register",
            json={
                "email": "old@example.com",
                "password": "password123",
                "name": "Test",
                "surname": "User",
            },
        )
        assert registered.status_code == 200
        session = sessionmaker(bind=engine)()
        user = session.query(User).filter_by(email="old@example.com").one()
        user.email_verified = True
        session.commit()
        session.close()

        rejected = client.post(
            "/auth/change-email",
            json={"new_email": "new@example.com", "password": "incorrect-password"},
        )
        assert rejected.status_code == 401

        changed = client.post(
            "/auth/change-email",
            json={"new_email": "NEW@example.com", "password": "password123"},
        )
        assert changed.status_code == 200
        assert verification_sent == ["new@example.com"]
        assert any(
            "access_token=" in value and "Max-Age=0" in value
            for value in changed.headers.get_list("set-cookie")
        )

        session = sessionmaker(bind=engine)()
        changed_user = session.query(User).filter_by(email="new@example.com").one()
        assert changed_user.email_verified is False
        session.close()
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
