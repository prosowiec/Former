"""FastAPI application bootstrap.

Endpoint implementations live in ``former.backend.routers``. This module owns
only application lifecycle, middleware, and router registration.
"""

import stripe
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .dependencies import get_current_user, get_verified_user
from .routers import airflow_router, auth_router, billing_router, health_router
from ..config import (
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    FRONTEND_URL,
    IS_LOCAL,
    SECRET_KEY,
    STRIPE_SECRET_KEY,
    TRUSTED_HOSTS,
    validate_production_security,
)

validate_production_security()


app = FastAPI(
    title="Former Airflow Trigger API",
    description="Trigger the Airflow form filler DAG with a form URL.",
    version="0.1.0",
)

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["http://localhost:5173", "http://localhost", "http://127.0.0.1", FRONTEND_URL]
        if IS_LOCAL
        else [FRONTEND_URL]
    ),
    allow_origin_regex=(
        r"^http://(localhost|127\.0\.0\.1|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$"
        if IS_LOCAL
        else None
    ),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site=COOKIE_SAMESITE,
    https_only=COOKIE_SECURE,
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(airflow_router)
app.include_router(billing_router)


__all__ = ["app", "get_current_user", "get_verified_user"]
