"""Enrollment service implementing registration business rules."""

from datetime import datetime
import os
import time
from typing import Callable, TypeVar

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.domain.schemas import CancelEnrollmentResponse, EnrollmentResponse
from app.repository.course_repository import CourseRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.student_repository import StudentRepository


MAX_CREDITS_PER_STUDENT = 18
RETRYABLE_LOCK_ERROR_CODES = {1205, 1213}
DEFAULT_LOCK_RETRY_ATTEMPTS = 3
DEFAULT_LOCK_RETRY_BACKOFF_SECONDS = 0.05

_T = TypeVar("_T")


def _int_env(name: str, default: int) -> int:
    """Read a positive integer environment variable with fallback."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _float_env(name: str, default: float) -> float:
    """Read a non-negative float environment variable with fallback."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


def _is_time_conflict(a_start, a_end, b_start, b_end) -> bool:
    """Return True when two time ranges overlap by at least one minute."""
    return a_start < b_end and b_start < a_end


class EnrollmentService:
    """Handle enrollment creation/cancellation with transactional safety."""

    def __init__(self) -> None:
        """Initialize repository dependencies."""
        self.student_repository = StudentRepository()
        self.course_repository = CourseRepository()
        self.enrollment_repository = EnrollmentRepository()

    def enroll(self, db: Session, student_id: int, course_id: int) -> EnrollmentResponse:
        """Enroll a student in a course after validating all constraints."""
        return self._run_with_lock_retry(
            operation="enroll",
            details={"student_id": student_id, "course_id": course_id},
            func=lambda: self._enroll_once(db, student_id, course_id),
        )

    def _enroll_once(self, db: Session, student_id: int, course_id: int) -> EnrollmentResponse:
        """Execute a single enrollment transaction attempt."""
        with db.begin():
            student = self.student_repository.get_by_id_for_update(db, student_id)
            if student is None:
                raise NotFoundException(
                    code="STUDENT_NOT_FOUND",
                    message="Student not found.",
                    details={"student_id": student_id},
                )

            course = self.course_repository.get_by_id_for_update(db, course_id)
            if course is None:
                raise NotFoundException(
                    code="COURSE_NOT_FOUND",
                    message="Course not found.",
                    details={"course_id": course_id},
                )

            if self.enrollment_repository.exists(db, student_id, course_id):
                raise ConflictException(
                    code="ALREADY_ENROLLED",
                    message="Student already enrolled in this course.",
                    details={"student_id": student_id, "course_id": course_id},
                )

            current_courses = self.enrollment_repository.list_student_courses(db, student_id)
            current_credits = sum(c.credits for c in current_courses)
            if current_credits + course.credits > MAX_CREDITS_PER_STUDENT:
                raise ConflictException(
                    code="CREDIT_LIMIT_EXCEEDED",
                    message="Credit limit exceeded.",
                    details={
                        "student_id": student_id,
                        "current_credits": current_credits,
                        "new_course_credits": course.credits,
                        "max_credits": MAX_CREDITS_PER_STUDENT,
                    },
                )

            for enrolled_course in current_courses:
                if enrolled_course.schedule_day != course.schedule_day:
                    continue
                if _is_time_conflict(
                    enrolled_course.start_time,
                    enrolled_course.end_time,
                    course.start_time,
                    course.end_time,
                ):
                    raise ConflictException(
                        code="SCHEDULE_CONFLICT",
                        message="Schedule conflict detected.",
                        details={
                            "student_id": student_id,
                            "course_id": course_id,
                            "conflict_course_id": enrolled_course.id,
                        },
                    )

            if course.enrolled >= course.capacity:
                raise ConflictException(
                    code="COURSE_FULL",
                    message="Course capacity is full.",
                    details={"course_id": course_id, "capacity": course.capacity},
                )

            enrollment = self.enrollment_repository.create(db, student_id, course_id)
            course.enrolled += 1
            db.flush()
            db.refresh(enrollment)

        return EnrollmentResponse(
            student_id=student_id,
            course_id=course_id,
            enrolled_at=enrollment.enrolled_at or datetime.utcnow(),
        )

    def cancel(self, db: Session, student_id: int, course_id: int) -> CancelEnrollmentResponse:
        """Cancel a student's enrollment and decrement enrolled count safely."""
        return self._run_with_lock_retry(
            operation="cancel",
            details={"student_id": student_id, "course_id": course_id},
            func=lambda: self._cancel_once(db, student_id, course_id),
        )

    def _cancel_once(self, db: Session, student_id: int, course_id: int) -> CancelEnrollmentResponse:
        """Execute a single cancellation transaction attempt."""
        with db.begin():
            student = self.student_repository.get_by_id_for_update(db, student_id)
            if student is None:
                raise NotFoundException(
                    code="STUDENT_NOT_FOUND",
                    message="Student not found.",
                    details={"student_id": student_id},
                )

            course = self.course_repository.get_by_id_for_update(db, course_id)
            if course is None:
                raise NotFoundException(
                    code="COURSE_NOT_FOUND",
                    message="Course not found.",
                    details={"course_id": course_id},
                )

            deleted = self.enrollment_repository.delete(db, student_id, course_id)
            if not deleted:
                raise NotFoundException(
                    code="ENROLLMENT_NOT_FOUND",
                    message="Enrollment not found.",
                    details={"student_id": student_id, "course_id": course_id},
                )

            if course.enrolled > 0:
                course.enrolled -= 1
            db.flush()

        return CancelEnrollmentResponse(student_id=student_id, course_id=course_id, canceled=True)

    def _run_with_lock_retry(
        self,
        *,
        operation: str,
        details: dict[str, object],
        func: Callable[[], _T],
    ) -> _T:
        """Retry transaction when MySQL lock timeout/deadlock is detected."""
        max_attempts = _int_env("ENROLLMENT_LOCK_RETRY_ATTEMPTS", DEFAULT_LOCK_RETRY_ATTEMPTS)
        backoff_seconds = _float_env(
            "ENROLLMENT_LOCK_RETRY_BACKOFF_SECONDS",
            DEFAULT_LOCK_RETRY_BACKOFF_SECONDS,
        )

        for attempt in range(1, max_attempts + 1):
            try:
                return func()
            except OperationalError as exc:
                db_error_code = _db_error_code(exc)
                if db_error_code not in RETRYABLE_LOCK_ERROR_CODES:
                    raise
                if attempt >= max_attempts:
                    raise ConflictException(
                        code="CONCURRENCY_RETRY_EXHAUSTED",
                        message="Concurrent update conflict. Please retry.",
                        details={
                            **details,
                            "operation": operation,
                            "attempts": attempt,
                            "db_error_code": db_error_code,
                        },
                    ) from exc
                time.sleep(backoff_seconds * attempt)

        raise RuntimeError("Unreachable retry state")


def _db_error_code(exc: OperationalError) -> int | None:
    """Extract MySQL DB-API error code from SQLAlchemy OperationalError."""
    original = getattr(exc, "orig", None)
    args = getattr(original, "args", ())
    if not args:
        return None
    try:
        return int(args[0])
    except (TypeError, ValueError):
        return None
