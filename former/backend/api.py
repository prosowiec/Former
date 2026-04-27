import secrets
from typing import Annotated, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware

from .auth import build_google_login_url, get_google_user_from_code, create_token_pair, verify_token, create_access_token
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
from .users import authenticate_user, create_user, get_user, get_or_create_oauth_user
from .db import get_db, init_db
from datetime import datetime, timedelta

# Security scheme for bearer token
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> Dict:
    """Dependency to get current user from JWT token in Authorization header."""
    
    print("ALL INFO" , credentials)
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = get_user(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

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


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login", response_model=AuthLoginResponse)
def auth_login(credentials: AuthLoginRequest):
    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create token pair
    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
    
    return AuthLoginResponse(
        user=UserResponse(**user),
        tokens=TokenResponse(**tokens)
    )

@app.get("/auth/tokens")
def auth_tokens(request: Request):
    """Exchange httpOnly OAuth cookies for tokens the frontend can store."""
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    
    if not access_token or not refresh_token:
        raise HTTPException(status_code=401, detail="No tokens found")
    
    response = JSONResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
    })
    # Clear the httpOnly cookies — frontend takes over storage from here
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@app.post("/auth/register", response_model=AuthLoginResponse)
def auth_register(credentials: AuthRegisterRequest):
    print(f"Attempting to register user: {credentials.email}")
    if get_user(credentials.email):
        raise HTTPException(status_code=400, detail="User already exists")

    user = create_user(credentials.email, credentials.password, credentials.name, credentials.surname)
    
    # Create token pair
    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))
    
    return AuthLoginResponse(
        user=UserResponse(**user),
        tokens=TokenResponse(**tokens)
    )


@app.get("/auth/google")
def auth_google_login(request: Request):
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state  # store in session, not a separate cookie
    google_login_url = build_google_login_url(state)
    return RedirectResponse(url=google_login_url)


@app.get("/auth/callback")
def auth_callback(request: Request):
    print("ALL COOKIES:", dict(request.cookies))

    state = request.query_params.get("state")
    code = request.query_params.get("code")
    stored_state = request.session.get("oauth_state")  # read from session

    if not state or not code:
        raise HTTPException(status_code=400, detail="Missing OAuth callback parameters")

    if not stored_state or state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    # Consume the state
    del request.session["oauth_state"]

    google_user_info = get_google_user_from_code(code)
    user = get_or_create_oauth_user(
        email=google_user_info["email"],
        name=google_user_info.get("name"),
        surname=google_user_info.get("surname"),
        google_id=google_user_info.get("sub")
    )

    tokens = create_token_pair(user["email"], user.get("name"), user.get("surname"))

    response = RedirectResponse(url=f"{FRONTEND_URL}/oauth-success")
    response.set_cookie(key="access_token", value=tokens["access_token"],
                        httponly=True, secure=False, samesite="lax")
    response.set_cookie(key="refresh_token", value=tokens["refresh_token"],
                        httponly=True, secure=False, samesite="lax")

    return response

@app.post("/auth/refresh", response_model=TokenResponse)
def auth_refresh(refresh_data: RefreshTokenRequest):
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
        
        return TokenResponse(**tokens)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token refresh failed")


@app.get("/auth/me")
def auth_me(current_user: Annotated[Dict, Depends(get_current_user)]):
    """Get current authenticated user."""
    return JSONResponse({"user": current_user})


@app.post("/auth/logout")
def auth_logout():
    """Logout endpoint - client should discard tokens."""
    # Since we're using JWT tokens (stateless), logout is handled client-side
    # by removing tokens from storage. Server-side token invalidation would
    # require a token blacklist, which adds complexity.
    return JSONResponse({"detail": "Logged out"})


@app.post("/airflow/trigger", response_model=AirflowTriggerResponse)
def airflow_trigger(
    payload: AirflowTriggerRequest,
    current_user: Annotated[Dict, Depends(get_current_user)]
) -> AirflowTriggerResponse:
    """Trigger an Airflow DAG. Requires JWT authentication."""
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
