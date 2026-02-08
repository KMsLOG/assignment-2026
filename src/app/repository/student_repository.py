"""Student persistence queries."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repository.models import Student


class StudentRepository:
    """Data access object for student entities."""

    def list_students(self, db: Session, limit: int, cursor: int | None) -> list[Student]:
        """Fetch student rows ordered by ID with cursor pagination."""
        stmt = select(Student)
        if cursor is not None:
            stmt = stmt.where(Student.id > cursor)
        stmt = stmt.order_by(Student.id).limit(limit + 1)
        return list(db.scalars(stmt))

    def get_by_id(self, db: Session, student_id: int) -> Student | None:
        """Fetch a student by primary key."""
        stmt = select(Student).where(Student.id == student_id)
        return db.scalar(stmt)

    def get_by_id_for_update(self, db: Session, student_id: int) -> Student | None:
        """Fetch and lock a student row for transaction-safe updates."""
        stmt = select(Student).where(Student.id == student_id).with_for_update()
        return db.scalar(stmt)
