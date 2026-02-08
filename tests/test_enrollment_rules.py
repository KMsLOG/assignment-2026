from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import time

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy import func, select

from app.core.exceptions import ConflictException
from app.main import app
from app.repository.database import SessionLocal
from app.repository.models import Course, Enrollment
from app.services.enrollment_service import EnrollmentService


class _FakeMySQLError(Exception):
    """Test helper to emulate DB-API MySQL errors with numeric code."""


def test_enroll_cancel_and_timetable_flow(client, test_data_factory) -> None:
    department_id = test_data_factory.create_department()
    professor_id = test_data_factory.create_professor(department_id)
    student_id = test_data_factory.create_student(department_id)
    course_id = test_data_factory.create_course(
        department_id=department_id,
        professor_id=professor_id,
        credits=3,
        capacity=30,
        schedule_day="MON",
        start_time=time(9, 0),
        end_time=time(10, 30),
    )

    enroll = client.post("/api/enrollments", json={"student_id": student_id, "course_id": course_id})
    assert enroll.status_code == 200
    enroll_body = enroll.json()
    assert enroll_body["student_id"] == student_id
    assert enroll_body["course_id"] == course_id

    duplicate = client.post("/api/enrollments", json={"student_id": student_id, "course_id": course_id})
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "ALREADY_ENROLLED"

    timetable = client.get(f"/api/students/{student_id}/timetable")
    assert timetable.status_code == 200
    assert any(course["id"] == course_id for course in timetable.json())

    cancel = client.delete(f"/api/enrollments/{student_id}/{course_id}")
    assert cancel.status_code == 200
    assert cancel.json()["canceled"] is True

    cancel_again = client.delete(f"/api/enrollments/{student_id}/{course_id}")
    assert cancel_again.status_code == 404
    assert cancel_again.json()["code"] == "ENROLLMENT_NOT_FOUND"


def test_credit_limit_exceeded(client, test_data_factory) -> None:
    department_id = test_data_factory.create_department()
    professor_id = test_data_factory.create_professor(department_id)
    student_id = test_data_factory.create_student(department_id)

    slots = [
        ("MON", time(9, 0), time(10, 30)),
        ("MON", time(10, 30), time(12, 0)),
        ("MON", time(13, 0), time(14, 30)),
        ("TUE", time(9, 0), time(10, 30)),
        ("TUE", time(10, 30), time(12, 0)),
        ("TUE", time(13, 0), time(14, 30)),
    ]

    course_ids: list[int] = []
    for day, start, end in slots:
        course_ids.append(
            test_data_factory.create_course(
                department_id=department_id,
                professor_id=professor_id,
                credits=3,
                capacity=30,
                schedule_day=day,
                start_time=start,
                end_time=end,
            )
        )

    extra_course_id = test_data_factory.create_course(
        department_id=department_id,
        professor_id=professor_id,
        credits=1,
        capacity=30,
        schedule_day="WED",
        start_time=time(9, 0),
        end_time=time(10, 30),
    )

    for course_id in course_ids:
        response = client.post("/api/enrollments", json={"student_id": student_id, "course_id": course_id})
        assert response.status_code == 200

    overflow = client.post("/api/enrollments", json={"student_id": student_id, "course_id": extra_course_id})
    assert overflow.status_code == 409
    assert overflow.json()["code"] == "CREDIT_LIMIT_EXCEEDED"


def test_schedule_conflict_with_one_minute_overlap(client, test_data_factory) -> None:
    department_id = test_data_factory.create_department()
    professor_id = test_data_factory.create_professor(department_id)
    student_id = test_data_factory.create_student(department_id)

    first_course_id = test_data_factory.create_course(
        department_id=department_id,
        professor_id=professor_id,
        credits=3,
        capacity=30,
        schedule_day="THU",
        start_time=time(9, 0),
        end_time=time(10, 30),
    )
    second_course_id = test_data_factory.create_course(
        department_id=department_id,
        professor_id=professor_id,
        credits=2,
        capacity=30,
        schedule_day="THU",
        start_time=time(10, 29),
        end_time=time(11, 30),
    )

    first = client.post("/api/enrollments", json={"student_id": student_id, "course_id": first_course_id})
    assert first.status_code == 200

    conflict = client.post("/api/enrollments", json={"student_id": student_id, "course_id": second_course_id})
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "SCHEDULE_CONFLICT"


def test_concurrency_allows_only_one_success_for_one_remaining_seat(test_data_factory) -> None:
    department_id = test_data_factory.create_department()
    professor_id = test_data_factory.create_professor(department_id)
    course_id = test_data_factory.create_course(
        department_id=department_id,
        professor_id=professor_id,
        credits=3,
        capacity=1,
        schedule_day="FRI",
        start_time=time(13, 0),
        end_time=time(14, 30),
    )

    student_ids = [test_data_factory.create_student(department_id) for _ in range(30)]
    service = EnrollmentService()

    def worker(student_id: int) -> str:
        with SessionLocal() as db:
            try:
                service.enroll(db, student_id, course_id)
                return "success"
            except ConflictException:
                return "conflict"

    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(worker, student_ids))

    assert results.count("success") == 1
    assert results.count("conflict") == 29

    with SessionLocal() as db:
        enrolled = db.scalar(select(Course.enrolled).where(Course.id == course_id))
        enrolled_rows = db.scalar(
            select(func.count()).select_from(Enrollment).where(Enrollment.course_id == course_id)
        )

    assert enrolled == 1
    assert enrolled_rows == 1


def test_api_concurrency_allows_only_one_success_for_one_remaining_seat(test_data_factory) -> None:
    department_id = test_data_factory.create_department()
    professor_id = test_data_factory.create_professor(department_id)
    course_id = test_data_factory.create_course(
        department_id=department_id,
        professor_id=professor_id,
        credits=3,
        capacity=1,
        schedule_day="WED",
        start_time=time(15, 0),
        end_time=time(16, 30),
    )

    student_ids = [test_data_factory.create_student(department_id) for _ in range(20)]

    def worker(student_id: int) -> str:
        with TestClient(app) as local_client:
            response = local_client.post(
                "/api/enrollments",
                json={"student_id": student_id, "course_id": course_id},
            )

        if response.status_code == 200:
            return "success"
        if response.status_code == 409 and response.json().get("code") == "COURSE_FULL":
            return "course_full"
        return f"unexpected:{response.status_code}:{response.text}"

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(worker, student_ids))

    assert results.count("success") == 1
    assert results.count("course_full") == 19

    with SessionLocal() as db:
        enrolled = db.scalar(select(Course.enrolled).where(Course.id == course_id))
        enrolled_rows = db.scalar(
            select(func.count()).select_from(Enrollment).where(Enrollment.course_id == course_id)
        )

    assert enrolled == 1
    assert enrolled_rows == 1


def test_retry_recovers_from_single_deadlock(monkeypatch, test_data_factory) -> None:
    department_id = test_data_factory.create_department()
    professor_id = test_data_factory.create_professor(department_id)
    student_id = test_data_factory.create_student(department_id)
    course_id = test_data_factory.create_course(
        department_id=department_id,
        professor_id=professor_id,
        credits=3,
        capacity=30,
        schedule_day="MON",
        start_time=time(9, 0),
        end_time=time(10, 30),
    )

    service = EnrollmentService()
    original_get_for_update = service.course_repository.get_by_id_for_update
    calls = {"count": 0}

    def flaky_get_for_update(db, lookup_course_id):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OperationalError(
                "SELECT ... FOR UPDATE",
                {},
                _FakeMySQLError(1213, "Deadlock found when trying to get lock"),
            )
        return original_get_for_update(db, lookup_course_id)

    monkeypatch.setattr(service.course_repository, "get_by_id_for_update", flaky_get_for_update)
    monkeypatch.setattr("app.services.enrollment_service.time.sleep", lambda _: None)

    with SessionLocal() as db:
        result = service.enroll(db, student_id, course_id)

    assert result.student_id == student_id
    assert result.course_id == course_id
    assert calls["count"] == 2


def test_retry_recovers_from_single_lock_timeout(monkeypatch, test_data_factory) -> None:
    department_id = test_data_factory.create_department()
    professor_id = test_data_factory.create_professor(department_id)
    student_id = test_data_factory.create_student(department_id)
    course_id = test_data_factory.create_course(
        department_id=department_id,
        professor_id=professor_id,
        credits=3,
        capacity=30,
        schedule_day="WED",
        start_time=time(11, 0),
        end_time=time(12, 30),
    )

    service = EnrollmentService()
    original_get_for_update = service.course_repository.get_by_id_for_update
    calls = {"count": 0}

    def flaky_get_for_update(db, lookup_course_id):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OperationalError(
                "SELECT ... FOR UPDATE",
                {},
                _FakeMySQLError(1205, "Lock wait timeout exceeded"),
            )
        return original_get_for_update(db, lookup_course_id)

    monkeypatch.setattr(service.course_repository, "get_by_id_for_update", flaky_get_for_update)
    monkeypatch.setattr("app.services.enrollment_service.time.sleep", lambda _: None)

    with SessionLocal() as db:
        result = service.enroll(db, student_id, course_id)

    assert result.student_id == student_id
    assert result.course_id == course_id
    assert calls["count"] == 2


def test_retry_exhaustion_returns_conflict(monkeypatch, test_data_factory) -> None:
    department_id = test_data_factory.create_department()
    professor_id = test_data_factory.create_professor(department_id)
    student_id = test_data_factory.create_student(department_id)
    course_id = test_data_factory.create_course(
        department_id=department_id,
        professor_id=professor_id,
        credits=3,
        capacity=30,
        schedule_day="TUE",
        start_time=time(9, 0),
        end_time=time(10, 30),
    )

    service = EnrollmentService()

    def always_deadlock(_, __):
        raise OperationalError(
            "SELECT ... FOR UPDATE",
            {},
            _FakeMySQLError(1213, "Deadlock found when trying to get lock"),
        )

    monkeypatch.setattr(service.course_repository, "get_by_id_for_update", always_deadlock)
    monkeypatch.setattr("app.services.enrollment_service.time.sleep", lambda _: None)

    with SessionLocal() as db:
        with pytest.raises(ConflictException) as caught:
            service.enroll(db, student_id, course_id)

    assert caught.value.code == "CONCURRENCY_RETRY_EXHAUSTED"
    assert caught.value.details["attempts"] == 3
    assert caught.value.details["db_error_code"] == 1213


def test_retry_exhaustion_uses_env_attempts(monkeypatch, test_data_factory) -> None:
    department_id = test_data_factory.create_department()
    professor_id = test_data_factory.create_professor(department_id)
    student_id = test_data_factory.create_student(department_id)
    course_id = test_data_factory.create_course(
        department_id=department_id,
        professor_id=professor_id,
        credits=3,
        capacity=30,
        schedule_day="FRI",
        start_time=time(9, 0),
        end_time=time(10, 30),
    )

    service = EnrollmentService()
    monkeypatch.setenv("ENROLLMENT_LOCK_RETRY_ATTEMPTS", "2")
    monkeypatch.setenv("ENROLLMENT_LOCK_RETRY_BACKOFF_SECONDS", "0")

    def always_deadlock(_, __):
        raise OperationalError(
            "SELECT ... FOR UPDATE",
            {},
            _FakeMySQLError(1213, "Deadlock found when trying to get lock"),
        )

    monkeypatch.setattr(service.course_repository, "get_by_id_for_update", always_deadlock)
    monkeypatch.setattr("app.services.enrollment_service.time.sleep", lambda _: None)

    with SessionLocal() as db:
        with pytest.raises(ConflictException) as caught:
            service.enroll(db, student_id, course_id)

    assert caught.value.code == "CONCURRENCY_RETRY_EXHAUSTED"
    assert caught.value.details["attempts"] == 2
    assert caught.value.details["db_error_code"] == 1213
