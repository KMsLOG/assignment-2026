from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.domain.schemas import CancelEnrollmentResponse, EnrollmentResponse
from app.repository.course_repository import CourseRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.student_repository import StudentRepository


MAX_CREDITS_PER_STUDENT = 18


def _is_time_conflict(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


class EnrollmentService:
    def __init__(self) -> None:
        self.student_repository = StudentRepository()
        self.course_repository = CourseRepository()
        self.enrollment_repository = EnrollmentRepository()

    def enroll(self, db: Session, student_id: int, course_id: int) -> EnrollmentResponse:
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
