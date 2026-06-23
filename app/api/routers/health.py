"""Liveness/readiness endpoints. These are public (no auth) by design."""

from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Return service liveness. Does not touch external dependencies."""
    return HealthResponse(status="ok", version=__version__)
