"""Student-related API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_catalog_service, get_db
from app.domain.schemas import CourseResponse, ErrorResponse, StudentListResponse
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get(
    "",
    response_model=StudentListResponse,
    responses={400: {"model": ErrorResponse}},
)
def list_students(
    db: Annotated[Session, Depends(get_db)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    cursor: Annotated[int | None, Query(ge=1)] = None,
) -> StudentListResponse:
    """List students with cursor-based pagination."""
    return catalog_service.list_students(db, limit, cursor)


@router.get(
    "/{student_id}/timetable",
    response_model=list[CourseResponse],
    responses={404: {"model": ErrorResponse}},
)
def get_timetable(
    student_id: int,
    db: Annotated[Session, Depends(get_db)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> list[CourseResponse]:
    """Return the current semester timetable for a single student."""
    return catalog_service.get_student_timetable(db, student_id)
