"""Domain routers for the Former API."""

from .airflow import router as airflow_router
from .auth import router as auth_router
from .billing import router as billing_router
from .health import router as health_router

__all__ = ["airflow_router", "auth_router", "billing_router", "health_router"]
