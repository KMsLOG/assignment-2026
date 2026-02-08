from __future__ import annotations

import re


def test_health_returns_seed_status(client) -> None:
    response = client.get("/health", headers={"X-Request-Id": "test-health-req"})
    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "test-health-req"
    assert int(response.headers["X-Process-Time-Ms"]) >= 0
    body = response.json()
    assert body["status"] == "ok"
    assert body["seed"]["completed"] is True
    assert body["seed"]["counts"]["departments"] >= 10
    assert body["seed"]["counts"]["professors"] >= 100
    assert body["seed"]["counts"]["courses"] >= 500
    assert body["seed"]["counts"]["students"] >= 10000


def test_list_students_professors_courses_with_department_filter(client) -> None:
    students_response = client.get("/api/students", params={"limit": 5})
    assert students_response.status_code == 200
    students_page = students_response.json()
    students = students_page["items"]
    assert len(students) == 5
    assert students_page["next_cursor"] is not None
    assert {"id", "student_no", "name", "department_id", "grade"} <= set(students[0].keys())

    next_students_response = client.get(
        "/api/students",
        params={"limit": 5, "cursor": students_page["next_cursor"]},
    )
    assert next_students_response.status_code == 200
    next_students = next_students_response.json()["items"]
    assert len(next_students) == 5
    assert next_students[0]["id"] > students[-1]["id"]

    professors_response = client.get("/api/professors", params={"limit": 5})
    assert professors_response.status_code == 200
    professors_page = professors_response.json()
    professors = professors_page["items"]
    assert len(professors) == 5
    assert professors_page["next_cursor"] is not None
    assert {"id", "professor_no", "name", "email", "department_id"} <= set(professors[0].keys())

    courses_response = client.get("/api/courses", params={"limit": 20})
    assert courses_response.status_code == 200
    courses_page = courses_response.json()
    courses = courses_page["items"]
    assert len(courses) == 20
    assert courses_page["next_cursor"] is not None

    required_course_fields = {"id", "name", "credits", "capacity", "enrolled", "schedule"}
    assert required_course_fields <= set(courses[0].keys())
    assert re.match(r"^.+ \d{2}:\d{2}-\d{2}:\d{2}$", courses[0]["schedule"])

    department_id = courses[0]["department_id"]
    filtered = client.get("/api/courses", params={"department_id": department_id, "limit": 50})
    assert filtered.status_code == 200
    filtered_courses = filtered.json()["items"]
    assert len(filtered_courses) > 0
    assert all(course["department_id"] == department_id for course in filtered_courses)


def test_invalid_pagination_returns_400(client) -> None:
    response = client.get("/api/students", params={"limit": 0})
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"

    response = client.get("/api/students", params={"cursor": 0})
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"
