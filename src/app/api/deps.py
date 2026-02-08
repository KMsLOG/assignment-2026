from sqlalchemy.orm import Session

from app.repository.database import get_db_session
from app.services.catalog_service import CatalogService
from app.services.enrollment_service import EnrollmentService


def get_db() -> Session:
    yield from get_db_session()


def get_catalog_service() -> CatalogService:
    return CatalogService()


def get_enrollment_service() -> EnrollmentService:
    return EnrollmentService()
