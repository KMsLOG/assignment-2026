"""Professor-related API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_catalog_service, get_db
from app.domain.schemas import ErrorResponse, ProfessorListResponse
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/api/professors", tags=["professors"])


@router.get(
    "",
    response_model=ProfessorListResponse,
    responses={400: {"model": ErrorResponse}},
)
def list_professors(
    db: Annotated[Session, Depends(get_db)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    cursor: Annotated[int | None, Query(ge=1)] = None,
) -> ProfessorListResponse:
    """List professors with cursor-based pagination."""
    return catalog_service.list_professors(db, limit, cursor)
