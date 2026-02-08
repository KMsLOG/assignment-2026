"""Pydantic schemas for API requests/responses and formatting helpers."""

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
    """Format class schedule to a readable text form."""
    day_kr = DAY_TO_KR.get(day, day)
    return f"{day_kr} {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"


class ErrorResponse(BaseModel):
    """Standard error payload returned by the API."""

    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class StudentResponse(BaseModel):
    """Student response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_no: str
    name: str
    department_id: int
    grade: int


class ProfessorResponse(BaseModel):
    """Professor response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    professor_no: str
    name: str
    email: str
    department_id: int


class CourseResponse(BaseModel):
    """Course response schema including occupancy and schedule."""

    id: int
    name: str
    credits: int
    capacity: int
    enrolled: int
    schedule: str
    department_id: int
    professor_id: int


class StudentListResponse(BaseModel):
    """Cursor-based student list response."""

    items: list[StudentResponse]
    next_cursor: int | None


class ProfessorListResponse(BaseModel):
    """Cursor-based professor list response."""

    items: list[ProfessorResponse]
    next_cursor: int | None


class CourseListResponse(BaseModel):
    """Cursor-based course list response."""

    items: list[CourseResponse]
    next_cursor: int | None


class EnrollmentRequest(BaseModel):
    """Payload for enrollment creation."""

    student_id: int = Field(ge=1)
    course_id: int = Field(ge=1)


class EnrollmentResponse(BaseModel):
    """Enrollment creation result payload."""

    student_id: int
    course_id: int
    enrolled_at: datetime


class CancelEnrollmentResponse(BaseModel):
    """Enrollment cancellation result payload."""

    student_id: int
    course_id: int
    canceled: bool


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str
    seed: dict[str, object]
