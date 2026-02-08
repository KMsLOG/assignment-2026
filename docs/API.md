# API 명세 (Markdown)

본 문서는 `docs/openapi.yaml`과 동일한 내용을 Markdown으로 정리한 문서입니다.

- Base URL: `http://localhost:8000`
- 응답 Content-Type: `application/json`

## 공통 규칙

### 공통 에러 응답 형식
```json
{
  "code": "COURSE_FULL",
  "message": "Course capacity is full.",
  "details": {}
}
```

### 주요 에러 코드
- `INVALID_REQUEST` (400)
- `STUDENT_NOT_FOUND` (404)
- `COURSE_NOT_FOUND` (404)
- `ENROLLMENT_NOT_FOUND` (404)
- `ALREADY_ENROLLED` (409)
- `COURSE_FULL` (409)
- `CREDIT_LIMIT_EXCEEDED` (409)
- `SCHEDULE_CONFLICT` (409)
- `INTERNAL_SERVER_ERROR` (500)

## 1. 헬스체크

### `GET /health`
- 설명: 서버 상태 및 초기 데이터 생성 상태 확인
- 요청 바디: 없음

응답 `200 OK`
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

## 2. 학생

### `GET /api/students`
- 설명: 학생 목록 조회
- Query Parameters:
  - `limit` (선택, 기본 100, 최소 1, 최대 500)
  - `offset` (선택, 기본 0, 최소 0)

응답 `200 OK`
```json
[
  {
    "id": 1,
    "student_no": "2026000001",
    "name": "김민준",
    "department_id": 1,
    "grade": 2
  }
]
```

에러:
- `400 INVALID_REQUEST`

### `GET /api/students/{student_id}/timetable`
- 설명: 특정 학생의 이번 학기 시간표 조회
- Path Parameters:
  - `student_id` (필수, 정수, 최소 1)

응답 `200 OK`
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

에러:
- `404 STUDENT_NOT_FOUND`

예시:
```json
{
  "code": "STUDENT_NOT_FOUND",
  "message": "Student not found.",
  "details": {
    "student_id": 999999
  }
}
```

## 3. 교수

### `GET /api/professors`
- 설명: 교수 목록 조회
- Query Parameters:
  - `limit` (선택, 기본 100, 최소 1, 최대 500)
  - `offset` (선택, 기본 0, 최소 0)

응답 `200 OK`
```json
[
  {
    "id": 1,
    "professor_no": "PF000001",
    "name": "박서연",
    "email": "prof0001@univ.ac.kr",
    "department_id": 1
  }
]
```

에러:
- `400 INVALID_REQUEST`

## 4. 강좌

### `GET /api/courses`
- 설명: 강좌 목록 조회 (전체/학과별)
- Query Parameters:
  - `department_id` (선택, 정수, 최소 1)
  - `limit` (선택, 기본 100, 최소 1, 최대 500)
  - `offset` (선택, 기본 0, 최소 0)

응답 `200 OK`
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

에러:
- `400 INVALID_REQUEST`

## 5. 수강신청

### `POST /api/enrollments`
- 설명: 학생이 특정 강좌를 수강신청
- 요청 바디:
```json
{
  "student_id": 1,
  "course_id": 10
}
```

응답 `200 OK`
```json
{
  "student_id": 1,
  "course_id": 10,
  "enrolled_at": "2026-02-08T06:20:00.000000"
}
```

에러:
- `400 INVALID_REQUEST`
- `404 STUDENT_NOT_FOUND`
- `404 COURSE_NOT_FOUND`
- `409 ALREADY_ENROLLED`
- `409 COURSE_FULL`
- `409 CREDIT_LIMIT_EXCEEDED`
- `409 SCHEDULE_CONFLICT`

에러 예시:
```json
{
  "code": "COURSE_FULL",
  "message": "Course capacity is full.",
  "details": {
    "course_id": 10,
    "capacity": 30
  }
}
```

## 6. 수강취소

### `DELETE /api/enrollments/{student_id}/{course_id}`
- 설명: 학생의 강좌 수강취소
- Path Parameters:
  - `student_id` (필수, 정수, 최소 1)
  - `course_id` (필수, 정수, 최소 1)

응답 `200 OK`
```json
{
  "student_id": 1,
  "course_id": 10,
  "canceled": true
}
```

에러:
- `404 STUDENT_NOT_FOUND`
- `404 COURSE_NOT_FOUND`
- `404 ENROLLMENT_NOT_FOUND`

에러 예시:
```json
{
  "code": "ENROLLMENT_NOT_FOUND",
  "message": "Enrollment not found.",
  "details": {
    "student_id": 1,
    "course_id": 10
  }
}
```

## 비즈니스 규칙
- 학생 최대 신청 학점: `18`
- 동일 학생 시간표 충돌 금지 (요일 동일 + 시간 1분이라도 겹치면 충돌)
- 정원 초과 금지
- 동시성 제어:
  - 수강신청/취소는 트랜잭션 단위 처리
  - `students`, `courses` 대상 `SELECT ... FOR UPDATE` 사용
  - 잔여 1석 동시 요청 시 1건만 성공하도록 설계

## 참고
- OpenAPI(Swagger) 원본: `docs/openapi.yaml`
