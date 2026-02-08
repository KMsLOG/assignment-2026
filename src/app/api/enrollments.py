from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_enrollment_service
from app.domain.schemas import (
    CancelEnrollmentResponse,
    EnrollmentRequest,
    EnrollmentResponse,
    ErrorResponse,
)
from app.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/api/enrollments", tags=["enrollments"])


@router.post(
    "",
    response_model=EnrollmentResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
def enroll(
    request: EnrollmentRequest,
    db: Annotated[Session, Depends(get_db)],
    enrollment_service: Annotated[EnrollmentService, Depends(get_enrollment_service)],
) -> EnrollmentResponse:
    return enrollment_service.enroll(db, request.student_id, request.course_id)


@router.delete(
    "/{student_id}/{course_id}",
    response_model=CancelEnrollmentResponse,
    responses={404: {"model": ErrorResponse}},
)
def cancel_enrollment(
    student_id: int,
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    enrollment_service: Annotated[EnrollmentService, Depends(get_enrollment_service)],
) -> CancelEnrollmentResponse:
    return enrollment_service.cancel(db, student_id, course_id)
