"""Dependency provider functions for FastAPI routes."""

from sqlalchemy.orm import Session

from app.repository.database import get_db_session
from app.services.catalog_service import CatalogService
from app.services.enrollment_service import EnrollmentService


def get_db() -> Session:
    """Provide a request-scoped SQLAlchemy session."""
    yield from get_db_session()


def get_catalog_service() -> CatalogService:
    """Provide a catalog service instance."""
    return CatalogService()


def get_enrollment_service() -> EnrollmentService:
    """Provide an enrollment service instance."""
    return EnrollmentService()
