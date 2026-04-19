import json
import os
from typing import Dict, Optional

from passlib.context import CryptContext

from .config import AUTH_USERS_FILE, DEFAULT_AUTH_USERNAME, DEFAULT_AUTH_PASSWORD

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def _ensure_user_store() -> None:
    if os.path.exists(AUTH_USERS_FILE):
        return

    users = {}
    if DEFAULT_AUTH_USERNAME and DEFAULT_AUTH_PASSWORD:
        users[DEFAULT_AUTH_USERNAME] = {
            "username": DEFAULT_AUTH_USERNAME,
            "password_hash": hash_password(DEFAULT_AUTH_PASSWORD),
        }

    os.makedirs(os.path.dirname(AUTH_USERS_FILE), exist_ok=True)
    with open(AUTH_USERS_FILE, "w", encoding="utf-8") as handler:
        json.dump(users, handler, indent=2)


def _load_user_store() -> Dict[str, dict]:
    _ensure_user_store()
    try:
        with open(AUTH_USERS_FILE, "r", encoding="utf-8") as handler:
            return json.load(handler)
    except (IOError, ValueError):
        return {}


def _save_user_store(users: Dict[str, dict]) -> None:
    os.makedirs(os.path.dirname(AUTH_USERS_FILE), exist_ok=True)
    with open(AUTH_USERS_FILE, "w", encoding="utf-8") as handler:
        json.dump(users, handler, indent=2)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def get_user(email: str) -> Optional[dict]:
    users = _load_user_store()
    return users.get(email)


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = get_user(email)
    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return {"email": user["email"], "name": user.get("name"), "surname": user.get("surname")}


def create_user(email: str, password: str, name: str, surname: str) -> dict:
    users = _load_user_store()
    if email in users:
        raise ValueError("User already exists")

    users[email] = {
        "email": email,
        "password_hash": hash_password(password),
        "name": name,
        "surname": surname,
    }
    _save_user_store(users)
    return {"email": email, "name": name, "surname": surname}
