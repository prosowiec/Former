import secrets
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from .auth import build_google_login_url, get_google_user_from_code, create_token_pair, verify_token
from .config import FRONTEND_URL, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from .dagOperations import trigger_airflow_dag
from .schemas import (
    AirflowTriggerRequest,
    AirflowTriggerResponse,
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthLoginResponse,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
)
from .users import authenticate_user, create_user, get_user
from datetime import datetime, timedelta

app = FastAPI(
    title="Former Airflow Trigger API",
    description="Trigger the Airflow form filler DAG with a form URL.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=False,
)


def get_current_user(request: Request):
    return request.session.get("user")


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=AuthLoginResponse)
def auth_login(request: Request, credentials: AuthLoginRequest):
    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create token pair
    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
    
    # Store in session
    request.session["user"] = user
    request.session["access_token"] = tokens["access_token"]
    request.session["refresh_token"] = tokens["refresh_token"]
    request.session["token_expires_at"] = (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()
    request.session["last_activity"] = datetime.utcnow().isoformat()
    
    return AuthLoginResponse(
        user=UserResponse(**user),
        tokens=TokenResponse(**tokens)
    )


@app.post("/auth/register", response_model=AuthLoginResponse)
def auth_register(request: Request, credentials: AuthRegisterRequest):
    if get_user(credentials.email):
        raise HTTPException(status_code=400, detail="User already exists")

    user = create_user(credentials.email, credentials.password, credentials.name, credentials.surname)
    
    # Create token pair
    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
    
    # Store in session
    request.session["user"] = user
    request.session["access_token"] = tokens["access_token"]
    request.session["refresh_token"] = tokens["refresh_token"]
    request.session["token_expires_at"] = (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()
    request.session["last_activity"] = datetime.utcnow().isoformat()
    
    return AuthLoginResponse(
        user=UserResponse(**user),
        tokens=TokenResponse(**tokens)
    )


@app.get("/auth/google")
def auth_google_login(request: Request):
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    return RedirectResponse(url=build_google_login_url(state))


@app.get("/auth/callback")
def auth_callback(request: Request):
    state = request.query_params.get("state")
    code = request.query_params.get("code")

    if not state or not code:
        raise HTTPException(status_code=400, detail="Missing OAuth callback parameters")

    if request.session.get("oauth_state") != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    user = get_google_user_from_code(code)
    
    # Create token pair for Google OAuth user
    tokens = create_token_pair(user["email"], user.get("name"))
    
    request.session["user"] = user
    request.session["access_token"] = tokens["access_token"]
    request.session["refresh_token"] = tokens["refresh_token"]
    request.session["token_expires_at"] = (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()
    request.session["last_activity"] = datetime.utcnow().isoformat()
    request.session.pop("oauth_state", None)

    return RedirectResponse(url=f"{FRONTEND_URL}/?login=success")


@app.post("/auth/refresh", response_model=TokenResponse)
def auth_refresh(request: Request, refresh_data: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        payload = verify_token(refresh_data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        email = payload.get("sub")
        user = get_user(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Create new token pair
        tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
        
        # Update session
        request.session["access_token"] = tokens["access_token"]
        request.session["refresh_token"] = tokens["refresh_token"]
        request.session["token_expires_at"] = (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()
        request.session["last_activity"] = datetime.utcnow().isoformat()
        
        return TokenResponse(**tokens)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token refresh failed")


@app.get("/auth/me")
def auth_me(request: Request):
    """Get current user with auto-refresh logic."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if token needs refresh
    token_expires_at_str = request.session.get("token_expires_at")
    if token_expires_at_str:
        token_expires_at = datetime.fromisoformat(token_expires_at_str)
        # Refresh if token expires in less than 5 minutes
        if datetime.utcnow() > token_expires_at - timedelta(minutes=5):
            try:
                refresh_token = request.session.get("refresh_token")
                if refresh_token:
                    payload = verify_token(refresh_token)
                    if payload.get("type") == "refresh":
                        tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
                        request.session["access_token"] = tokens["access_token"]
                        request.session["refresh_token"] = tokens["refresh_token"]
                        request.session["token_expires_at"] = (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()
            except:
                pass  # If refresh fails, continue with existing token
    
    # Update last activity
    request.session["last_activity"] = datetime.utcnow().isoformat()
    
    return JSONResponse({"user": user, "access_token": request.session.get("access_token")})


@app.post("/auth/logout")
def auth_logout(request: Request):
    request.session.clear()
    return JSONResponse({"detail": "Logged out"})


@app.post("/airflow/trigger", response_model=AirflowTriggerResponse)
def airflow_trigger(request: Request, payload: AirflowTriggerRequest) -> AirflowTriggerResponse:
    current_user = get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        response_payload = trigger_airflow_dag(
            str(payload.form_url),
            payload.dag_id,
            payload.run_id,
            payload.num_executions,
            payload.base_interval_minutes,
            payload.interval_jitter_minutes,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Airflow API error: {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to call Airflow API: {exc}")

    dag_run_id = response_payload.get("dag_run_id") or response_payload.get("dag_run", {}).get("dag_run_id", "")
    state = response_payload.get("state", "unknown")

    return AirflowTriggerResponse(
        dag_id=payload.dag_id,
        dag_run_id=dag_run_id,
        state=state,
        num_executions=payload.num_executions,
        base_interval_minutes=payload.base_interval_minutes,
        interval_jitter_minutes=payload.interval_jitter_minutes,
        airflow_response=response_payload,
    )
