from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_catalog_service, get_db
from app.domain.schemas import CourseResponse, ErrorResponse
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get(
    "",
    response_model=list[CourseResponse],
    responses={400: {"model": ErrorResponse}},
)
def list_courses(
    db: Annotated[Session, Depends(get_db)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    department_id: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CourseResponse]:
    return catalog_service.list_courses(
        db=db,
        limit=limit,
        offset=offset,
        department_id=department_id,
    )
