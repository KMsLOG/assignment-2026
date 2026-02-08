from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.repository.models import Course, Enrollment


class EnrollmentRepository:
    def exists(self, db: Session, student_id: int, course_id: int) -> bool:
        stmt = (
            select(Enrollment.student_id)
            .where(and_(Enrollment.student_id == student_id, Enrollment.course_id == course_id))
            .limit(1)
        )
        return db.scalar(stmt) is not None

    def create(self, db: Session, student_id: int, course_id: int) -> Enrollment:
        enrollment = Enrollment(student_id=student_id, course_id=course_id)
        db.add(enrollment)
        return enrollment

    def delete(self, db: Session, student_id: int, course_id: int) -> bool:
        stmt = select(Enrollment).where(
            and_(Enrollment.student_id == student_id, Enrollment.course_id == course_id)
        )
        enrollment = db.scalar(stmt)
        if enrollment is None:
            return False
        db.delete(enrollment)
        return True

    def list_student_courses(self, db: Session, student_id: int) -> list[Course]:
        stmt = (
            select(Course)
            .join(Enrollment, Enrollment.course_id == Course.id)
            .where(Enrollment.student_id == student_id)
            .order_by(Course.schedule_day, Course.start_time, Course.id)
        )
        return list(db.scalars(stmt))
