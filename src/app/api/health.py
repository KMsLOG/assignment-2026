"""Health check API endpoints."""

from fastapi import APIRouter, Request

from app.domain.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    """Return API availability and runtime seed status."""
    return HealthResponse(status="ok", seed=request.app.state.seed_status)
