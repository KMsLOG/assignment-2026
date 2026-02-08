"""Catalog service for read-only student/professor/course use cases."""

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.domain.schemas import (
    CourseListResponse,
    CourseResponse,
    ProfessorListResponse,
    ProfessorResponse,
    StudentListResponse,
    StudentResponse,
    format_schedule,
)
from app.repository.course_repository import CourseRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.professor_repository import ProfessorRepository
from app.repository.student_repository import StudentRepository


class CatalogService:
    """Coordinate catalog read operations across repository objects."""

    def __init__(self) -> None:
        """Initialize repository dependencies."""
        self.student_repository = StudentRepository()
        self.professor_repository = ProfessorRepository()
        self.course_repository = CourseRepository()
        self.enrollment_repository = EnrollmentRepository()

    def list_students(self, db: Session, limit: int, cursor: int | None) -> StudentListResponse:
        """Return one student page and the next cursor."""
        students = self.student_repository.list_students(db, limit, cursor)
        has_next = len(students) > limit
        students_page = students[:limit]
        return StudentListResponse(
            items=[StudentResponse.model_validate(student) for student in students_page],
            next_cursor=students_page[-1].id if has_next and students_page else None,
        )

    def list_professors(self, db: Session, limit: int, cursor: int | None) -> ProfessorListResponse:
        """Return one professor page and the next cursor."""
        professors = self.professor_repository.list_professors(db, limit, cursor)
        has_next = len(professors) > limit
        professors_page = professors[:limit]
        return ProfessorListResponse(
            items=[ProfessorResponse.model_validate(professor) for professor in professors_page],
            next_cursor=professors_page[-1].id if has_next and professors_page else None,
        )

    def list_courses(
        self,
        db: Session,
        limit: int,
        cursor: int | None,
        department_id: int | None = None,
    ) -> CourseListResponse:
        """Return one course page filtered by department when requested."""
        courses = self.course_repository.list_courses(db, limit, cursor, department_id)
        has_next = len(courses) > limit
        courses_page = courses[:limit]
        return CourseListResponse(
            items=[self._course_to_response(course) for course in courses_page],
            next_cursor=courses_page[-1].id if has_next and courses_page else None,
        )

    def get_student_timetable(self, db: Session, student_id: int) -> list[CourseResponse]:
        """Return all enrolled courses for a student in the current semester."""
        student = self.student_repository.get_by_id(db, student_id)
        if student is None:
            raise NotFoundException(
                code="STUDENT_NOT_FOUND",
                message="Student not found.",
                details={"student_id": student_id},
            )
        courses = self.enrollment_repository.list_student_courses(db, student_id)
        return [self._course_to_response(course) for course in courses]

    @staticmethod
    def _course_to_response(course) -> CourseResponse:
        """Convert a Course ORM entity to API response schema."""
        return CourseResponse(
            id=course.id,
            name=course.name,
            credits=course.credits,
            capacity=course.capacity,
            enrolled=course.enrolled,
            schedule=format_schedule(course.schedule_day, course.start_time, course.end_time),
            department_id=course.department_id,
            professor_id=course.professor_id,
        )
