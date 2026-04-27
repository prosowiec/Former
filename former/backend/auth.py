import httpx
from urllib.parse import urlencode
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt

from .config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_OAUTH_REDIRECT_URI,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_SCOPE = "openid email profile"


def build_google_login_url(state: str) -> str:
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_OAUTH_REDIRECT_URI:
        raise RuntimeError("Google OAuth is not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and GOOGLE_OAUTH_REDIRECT_URI.")

    query = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": GOOGLE_SCOPE,
        "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(query)}"


def exchange_code_for_token(code: str) -> dict:
    payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    with httpx.Client(timeout=20) as client:
        response = client.post(GOOGLE_TOKEN_URL, data=payload)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"Google token exchange failed: {exc.response.text}")
        return response.json()


def fetch_google_userinfo(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    with httpx.Client(timeout=20) as client:
        response = client.get(GOOGLE_USERINFO_URL, headers=headers)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"Google userinfo request failed: {exc.response.text}")
        return response.json()


def get_google_user_from_code(code: str) -> dict:
    token_data = exchange_code_for_token(code)
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=502, detail="Google did not return an access token")

    profile = fetch_google_userinfo(access_token)
    return {
        "email": profile.get("email"),
        "name": profile.get("given_name"),
        "surname": profile.get("family_name"),
        "picture": profile.get("picture"),
        "sub": profile.get("sub"),
    }


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def create_token_pair(email: str, name: Optional[str] = None, surname: Optional[str] = None) -> Dict[str, str]:
    """Create both access and refresh tokens for a user."""
    token_data = {"sub": email, "name": name, "surname": surname}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
