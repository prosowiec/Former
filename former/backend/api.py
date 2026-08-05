"""FastAPI application bootstrap.

Endpoint implementations live in ``former.backend.routers``. This module owns
only application lifecycle, middleware, and router registration.
"""

from contextlib import asynccontextmanager

import stripe
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .db import init_db
from .dependencies import get_current_user, get_verified_user
from .routers import airflow_router, auth_router, billing_router, health_router
from ..config import FRONTEND_URL, SECRET_KEY, STRIPE_SECRET_KEY


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as exc:
        print(f"Failed to initialize database: {exc}")
    yield


app = FastAPI(
    title="Former Airflow Trigger API",
    description="Trigger the Airflow form filler DAG with a form URL.",
    version="0.1.0",
    lifespan=lifespan,
)

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost",
        "http://127.0.0.1",
        FRONTEND_URL,
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$",
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

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(airflow_router)
app.include_router(billing_router)


__all__ = ["app", "get_current_user", "get_verified_user"]
