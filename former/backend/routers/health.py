"""Service health endpoints."""

from typing import Dict

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}
