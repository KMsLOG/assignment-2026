from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_catalog_service, get_db
from app.domain.schemas import CourseListResponse, ErrorResponse
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get(
    "",
    response_model=CourseListResponse,
    responses={400: {"model": ErrorResponse}},
)
def list_courses(
    db: Annotated[Session, Depends(get_db)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    department_id: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    cursor: Annotated[int | None, Query(ge=1)] = None,
) -> CourseListResponse:
    return catalog_service.list_courses(
        db=db,
        limit=limit,
        cursor=cursor,
        department_id=department_id,
    )
