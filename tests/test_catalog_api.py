from __future__ import annotations

import re


def test_health_returns_seed_status(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["seed"]["completed"] is True
    assert body["seed"]["counts"]["departments"] >= 10
    assert body["seed"]["counts"]["professors"] >= 100
    assert body["seed"]["counts"]["courses"] >= 500
    assert body["seed"]["counts"]["students"] >= 10000


def test_list_students_professors_courses_with_department_filter(client) -> None:
    students_response = client.get("/api/students", params={"limit": 5, "offset": 0})
    assert students_response.status_code == 200
    students = students_response.json()
    assert len(students) == 5
    assert {"id", "student_no", "name", "department_id", "grade"} <= set(students[0].keys())

    professors_response = client.get("/api/professors", params={"limit": 5, "offset": 0})
    assert professors_response.status_code == 200
    professors = professors_response.json()
    assert len(professors) == 5
    assert {"id", "professor_no", "name", "email", "department_id"} <= set(professors[0].keys())

    courses_response = client.get("/api/courses", params={"limit": 20, "offset": 0})
    assert courses_response.status_code == 200
    courses = courses_response.json()
    assert len(courses) == 20

    required_course_fields = {"id", "name", "credits", "capacity", "enrolled", "schedule"}
    assert required_course_fields <= set(courses[0].keys())
    assert re.match(r"^[월화수목금] \d{2}:\d{2}-\d{2}:\d{2}$", courses[0]["schedule"])

    department_id = courses[0]["department_id"]
    filtered = client.get("/api/courses", params={"department_id": department_id, "limit": 50, "offset": 0})
    assert filtered.status_code == 200
    filtered_courses = filtered.json()
    assert len(filtered_courses) > 0
    assert all(course["department_id"] == department_id for course in filtered_courses)


def test_invalid_pagination_returns_400(client) -> None:
    response = client.get("/api/students", params={"limit": 0})
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"
