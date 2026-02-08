# API Specification

Base URL: `http://localhost:8000`

## Common Error Format
```json
{
  "code": "COURSE_FULL",
  "message": "Course capacity is full.",
  "details": {}
}
```

## 1) Health Check
### `GET /health`
- Description: Server and seed status
- Response `200`
```json
{
  "status": "ok",
  "seed": {
    "completed": true,
    "seeded": true,
    "duration_ms": 734,
    "counts": {
      "departments": 12,
      "professors": 120,
      "courses": 600,
      "students": 10000
    }
  }
}
```

## 2) Students
### `GET /api/students`
- Query
  - `limit` (optional, default: 100, min 1, max 500)
  - `offset` (optional, default: 0, min 0)
- Response `200`
```json
[
  {
    "id": 1,
    "student_no": "2026000001",
    "name": "김민윤",
    "department_id": 1,
    "grade": 1
  }
]
```

### `GET /api/students/{student_id}/timetable`
- Response `200`
```json
[
  {
    "id": 1,
    "name": "자료구조 01분반",
    "credits": 3,
    "capacity": 30,
    "enrolled": 25,
    "schedule": "월 09:00-10:30",
    "department_id": 1,
    "professor_id": 1
  }
]
```
- Errors
  - `404 STUDENT_NOT_FOUND`

## 3) Professors
### `GET /api/professors`
- Query
  - `limit` (optional, default: 100, min 1, max 500)
  - `offset` (optional, default: 0, min 0)
- Response `200`
```json
[
  {
    "id": 1,
    "professor_no": "PF000001",
    "name": "김민윤",
    "email": "prof0001@univ.ac.kr",
    "department_id": 1
  }
]
```

## 4) Courses
### `GET /api/courses`
- Query
  - `department_id` (optional)
  - `limit` (optional, default: 100, min 1, max 500)
  - `offset` (optional, default: 0, min 0)
- Response `200`
```json
[
  {
    "id": 1,
    "name": "자료구조 01분반",
    "credits": 3,
    "capacity": 30,
    "enrolled": 25,
    "schedule": "월 09:00-10:30",
    "department_id": 1,
    "professor_id": 1
  }
]
```

## 5) Enroll
### `POST /api/enrollments`
- Request
```json
{
  "student_id": 1,
  "course_id": 10
}
```
- Response `200`
```json
{
  "student_id": 1,
  "course_id": 10,
  "enrolled_at": "2026-02-08T06:20:00.000000"
}
```
- Errors
  - `404 STUDENT_NOT_FOUND`
  - `404 COURSE_NOT_FOUND`
  - `409 ALREADY_ENROLLED`
  - `409 COURSE_FULL`
  - `409 CREDIT_LIMIT_EXCEEDED`
  - `409 SCHEDULE_CONFLICT`

## 6) Cancel Enrollment
### `DELETE /api/enrollments/{student_id}/{course_id}`
- Response `200`
```json
{
  "student_id": 1,
  "course_id": 10,
  "canceled": true
}
```
- Errors
  - `404 STUDENT_NOT_FOUND`
  - `404 COURSE_NOT_FOUND`
  - `404 ENROLLMENT_NOT_FOUND`

## Business Rules
- Max credits per student: `18`
- Schedule overlap for same student is not allowed
- Course capacity overflow is not allowed
- Concurrency control:
  - Enrollment/Cancellation is transaction-scoped
  - `SELECT ... FOR UPDATE` on student and course rows
  - prevents overbooking under concurrent requests
