from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load_env_file(path: Path) -> None:
    """Load KEY=VALUE pairs into environment unless already set."""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


for env_path in (ROOT / ".env", ROOT / ".env.example"):
    if env_path.exists():
        _load_env_file(env_path)
        break

os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", os.environ.get("MYSQL_DATABASE", "course_registration"))
os.environ.setdefault("DB_USER", os.environ.get("MYSQL_USER", "app"))
os.environ.setdefault("DB_PASSWORD", os.environ.get("MYSQL_PASSWORD", "app"))

from app.main import app, startup
from app.repository.database import SessionLocal
from app.repository.models import Course, Department, Enrollment, Professor, Student


@pytest.fixture(scope="session", autouse=True)
def ensure_seeded_database() -> None:
    startup()


@pytest.fixture(scope="session")
def client(ensure_seeded_database: None) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


class TestDataFactory:
    def __init__(self) -> None:
        self._seq = 0
        self._department_ids: list[int] = []
        self._professor_ids: list[int] = []
        self._student_ids: list[int] = []
        self._course_ids: list[int] = []

    def _next(self) -> int:
        self._seq += 1
        return self._seq

    def create_department(self) -> int:
        n = self._next()
        code = f"TD{n:06d}"
        name = f"테스트학과{n}"
        with SessionLocal() as db:
            department = Department(code=code, name=name)
            db.add(department)
            db.commit()
            db.refresh(department)
            self._department_ids.append(department.id)
            return department.id

    def create_professor(self, department_id: int) -> int:
        n = self._next()
        professor_no = f"TP{n:06d}"
        email = f"tp{n:06d}@test.local"
        with SessionLocal() as db:
            professor = Professor(
                professor_no=professor_no,
                name=f"테스트교수{n}",
                email=email,
                department_id=department_id,
            )
            db.add(professor)
            db.commit()
            db.refresh(professor)
            self._professor_ids.append(professor.id)
            return professor.id

    def create_student(self, department_id: int) -> int:
        n = self._next()
        student_no = f"9{n:09d}"
        with SessionLocal() as db:
            student = Student(
                student_no=student_no,
                name=f"테스트학생{n}",
                department_id=department_id,
                grade=((n - 1) % 4) + 1,
            )
            db.add(student)
            db.commit()
            db.refresh(student)
            self._student_ids.append(student.id)
            return student.id

    def create_course(
        self,
        *,
        department_id: int,
        professor_id: int,
        credits: int,
        capacity: int,
        schedule_day: str,
        start_time: time,
        end_time: time,
        name: str | None = None,
    ) -> int:
        n = self._next()
        course_code = f"TC{n:06d}"
        with SessionLocal() as db:
            course = Course(
                course_code=course_code,
                name=name or f"테스트강의{n}",
                credits=credits,
                capacity=capacity,
                enrolled=0,
                schedule_day=schedule_day,
                start_time=start_time,
                end_time=end_time,
                department_id=department_id,
                professor_id=professor_id,
                semester="2026-1",
            )
            db.add(course)
            db.commit()
            db.refresh(course)
            self._course_ids.append(course.id)
            return course.id

    def cleanup(self) -> None:
        with SessionLocal() as db:
            if self._course_ids:
                db.execute(delete(Enrollment).where(Enrollment.course_id.in_(self._course_ids)))
                db.execute(delete(Course).where(Course.id.in_(self._course_ids)))
            if self._student_ids:
                db.execute(delete(Enrollment).where(Enrollment.student_id.in_(self._student_ids)))
                db.execute(delete(Student).where(Student.id.in_(self._student_ids)))
            if self._professor_ids:
                db.execute(delete(Professor).where(Professor.id.in_(self._professor_ids)))
            if self._department_ids:
                db.execute(delete(Department).where(Department.id.in_(self._department_ids)))
            db.commit()


@pytest.fixture
def test_data_factory() -> Any:
    factory = TestDataFactory()
    try:
        yield factory
    finally:
        factory.cleanup()
