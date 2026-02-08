from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.domain.schemas import CourseResponse, ProfessorResponse, StudentResponse, format_schedule
from app.repository.course_repository import CourseRepository
from app.repository.enrollment_repository import EnrollmentRepository
from app.repository.professor_repository import ProfessorRepository
from app.repository.student_repository import StudentRepository


class CatalogService:
    def __init__(self) -> None:
        self.student_repository = StudentRepository()
        self.professor_repository = ProfessorRepository()
        self.course_repository = CourseRepository()
        self.enrollment_repository = EnrollmentRepository()

    def list_students(self, db: Session, limit: int, offset: int) -> list[StudentResponse]:
        students = self.student_repository.list_students(db, limit, offset)
        return [StudentResponse.model_validate(student) for student in students]

    def list_professors(self, db: Session, limit: int, offset: int) -> list[ProfessorResponse]:
        professors = self.professor_repository.list_professors(db, limit, offset)
        return [ProfessorResponse.model_validate(professor) for professor in professors]

    def list_courses(
        self,
        db: Session,
        limit: int,
        offset: int,
        department_id: int | None = None,
    ) -> list[CourseResponse]:
        courses = self.course_repository.list_courses(db, limit, offset, department_id)
        return [self._course_to_response(course) for course in courses]

    def get_student_timetable(self, db: Session, student_id: int) -> list[CourseResponse]:
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
