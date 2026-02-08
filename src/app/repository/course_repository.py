from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repository.models import Course


class CourseRepository:
    def list_courses(
        self,
        db: Session,
        limit: int,
        cursor: int | None,
        department_id: int | None = None,
    ) -> list[Course]:
        stmt = select(Course)
        if department_id is not None:
            stmt = stmt.where(Course.department_id == department_id)
        if cursor is not None:
            stmt = stmt.where(Course.id > cursor)
        stmt = stmt.order_by(Course.id).limit(limit + 1)
        return list(db.scalars(stmt))

    def get_by_id(self, db: Session, course_id: int) -> Course | None:
        stmt = select(Course).where(Course.id == course_id)
        return db.scalar(stmt)

    def get_by_id_for_update(self, db: Session, course_id: int) -> Course | None:
        stmt = select(Course).where(Course.id == course_id).with_for_update()
        return db.scalar(stmt)
