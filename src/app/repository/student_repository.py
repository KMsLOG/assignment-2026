from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repository.models import Student


class StudentRepository:
    def list_students(self, db: Session, limit: int, offset: int) -> list[Student]:
        stmt = select(Student).order_by(Student.id).limit(limit).offset(offset)
        return list(db.scalars(stmt))

    def get_by_id(self, db: Session, student_id: int) -> Student | None:
        stmt = select(Student).where(Student.id == student_id)
        return db.scalar(stmt)

    def get_by_id_for_update(self, db: Session, student_id: int) -> Student | None:
        stmt = select(Student).where(Student.id == student_id).with_for_update()
        return db.scalar(stmt)
