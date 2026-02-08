"""Dependency provider functions for FastAPI routes."""

import os
from collections.abc import Generator
from threading import BoundedSemaphore

from sqlalchemy.orm import Session

from app.core.exceptions import ServiceUnavailableException
from app.repository.database import get_db_session
from app.services.catalog_service import CatalogService
from app.services.enrollment_service import EnrollmentService


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


ENROLLMENT_MAX_INFLIGHT_REQUESTS = _int_env("ENROLLMENT_MAX_INFLIGHT_REQUESTS", 40)
_enrollment_request_semaphore = BoundedSemaphore(ENROLLMENT_MAX_INFLIGHT_REQUESTS)


def get_db() -> Session:
    """Provide a request-scoped SQLAlchemy session."""
    yield from get_db_session()


def get_catalog_service() -> CatalogService:
    """Provide a catalog service instance."""
    return CatalogService()


def get_enrollment_service() -> EnrollmentService:
    """Provide an enrollment service instance."""
    return EnrollmentService()


def get_enrollment_request_slot() -> Generator[None, None, None]:
    """Gate enrollment API requests with a fail-fast in-flight limit."""
    if not _enrollment_request_semaphore.acquire(blocking=False):
        raise ServiceUnavailableException(
            code="ENROLLMENT_REQUEST_LIMIT_REACHED",
            message="Enrollment API is busy. Please retry shortly.",
            details={"max_inflight_requests": ENROLLMENT_MAX_INFLIGHT_REQUESTS},
        )
    try:
        yield
    finally:
        _enrollment_request_semaphore.release()
