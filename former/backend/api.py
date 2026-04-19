import secrets
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from .auth import build_google_login_url, get_google_user_from_code
from .config import FRONTEND_URL, SECRET_KEY
from .dagOperations import trigger_airflow_dag
from .schemas import (
    AirflowTriggerRequest,
    AirflowTriggerResponse,
    AuthLoginRequest,
    AuthRegisterRequest,
)
from .users import authenticate_user, create_user, get_user

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


@app.post("/auth/login")
def auth_login(request: Request, credentials: AuthLoginRequest):
    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    request.session["user"] = user
    return JSONResponse({"detail": "Logged in"})


@app.post("/auth/register")
def auth_register(request: Request, credentials: AuthRegisterRequest):
    if get_user(credentials.email):
        raise HTTPException(status_code=400, detail="User already exists")

    create_user(credentials.email, credentials.password, credentials.name, credentials.surname)
    return JSONResponse({"detail": "User created"})


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
    request.session["user"] = user
    request.session.pop("oauth_state", None)

    return RedirectResponse(url=f"{FRONTEND_URL}/?login=success")


@app.get("/auth/me")
def auth_me(request: Request):
    return JSONResponse({"user": get_current_user(request)})


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
