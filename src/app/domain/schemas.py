from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field


DAY_TO_KR = {
    "MON": "월",
    "TUE": "화",
    "WED": "수",
    "THU": "목",
    "FRI": "금",
}


def format_schedule(day: str, start: time, end: time) -> str:
    day_kr = DAY_TO_KR.get(day, day)
    return f"{day_kr} {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_no: str
    name: str
    department_id: int
    grade: int


class ProfessorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    professor_no: str
    name: str
    email: str
    department_id: int


class CourseResponse(BaseModel):
    id: int
    name: str
    credits: int
    capacity: int
    enrolled: int
    schedule: str
    department_id: int
    professor_id: int


class EnrollmentRequest(BaseModel):
    student_id: int = Field(ge=1)
    course_id: int = Field(ge=1)


class EnrollmentResponse(BaseModel):
    student_id: int
    course_id: int
    enrolled_at: datetime


class CancelEnrollmentResponse(BaseModel):
    student_id: int
    course_id: int
    canceled: bool


class HealthResponse(BaseModel):
    status: str
    seed: dict[str, object]
