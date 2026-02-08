# API 명세 (Markdown)

이 문서는 `docs/openapi.yaml`의 내용을 Markdown으로 정리한 버전입니다.

- Base URL: `http://localhost:8000`
- Content-Type: `application/json`

## 공통 규칙

### 목록 조회 페이지네이션
- 목록 API는 커서 기반 페이지네이션을 사용합니다.
- 공통 쿼리 파라미터:
  - `limit`: 기본 `100`, 최소 `1`, 최대 `500`
  - `cursor`: 이전 응답의 `next_cursor` 값 (첫 페이지는 생략)
- 공통 응답 형태:

```json
{
  "items": [],
  "next_cursor": 100
}
```

- `next_cursor`가 `null`이면 마지막 페이지입니다.

### 공통 에러 응답 형식

```json
{
  "code": "INVALID_REQUEST",
  "message": "Request validation failed.",
  "details": {
    "errors": []
  }
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
- `CONCURRENCY_RETRY_EXHAUSTED` (409)
- `INTERNAL_SERVER_ERROR` (500)

## 1. 헬스체크

### `GET /health`
설명: 서버 상태와 초기 데이터 생성 상태 조회

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
설명: 학생 목록 조회 (ID 오름차순, 커서 페이지네이션)

쿼리 파라미터:
- `limit` (선택)
- `cursor` (선택)

응답 `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "student_no": "2026000001",
      "name": "김민준",
      "department_id": 1,
      "grade": 2
    }
  ],
  "next_cursor": 1
}
```

에러:
- `400 INVALID_REQUEST`

### `GET /api/students/{student_id}/timetable`
설명: 특정 학생의 이번 학기 시간표 조회

경로 파라미터:
- `student_id` (필수, 정수, 최소 1)

응답 `200 OK`

```json
[
  {
    "id": 101,
    "name": "자료구조 01분반",
    "credits": 3,
    "capacity": 40,
    "enrolled": 38,
    "schedule": "월 09:00-10:15",
    "department_id": 1,
    "professor_id": 12
  }
]
```

에러:
- `404 STUDENT_NOT_FOUND`

## 3. 교수

### `GET /api/professors`
설명: 교수 목록 조회 (ID 오름차순, 커서 페이지네이션)

쿼리 파라미터:
- `limit` (선택)
- `cursor` (선택)

응답 `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "professor_no": "PF000001",
      "name": "박서준",
      "email": "prof0001@univ.ac.kr",
      "department_id": 1
    }
  ],
  "next_cursor": 1
}
```

에러:
- `400 INVALID_REQUEST`

## 4. 강좌

### `GET /api/courses`
설명: 강좌 목록 조회 (전체/학과별, 정원/현재 인원/시간 포함)

쿼리 파라미터:
- `department_id` (선택, 정수, 최소 1)
- `limit` (선택)
- `cursor` (선택)

응답 `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "name": "자료구조 01분반",
      "credits": 3,
      "capacity": 40,
      "enrolled": 38,
      "schedule": "월 09:00-10:15",
      "department_id": 1,
      "professor_id": 3
    }
  ],
  "next_cursor": 1
}
```

에러:
- `400 INVALID_REQUEST`

## 5. 수강신청

### `POST /api/enrollments`
설명: 학생이 강좌를 수강신청

요청 바디:

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
- `409 CONCURRENCY_RETRY_EXHAUSTED`

예시 (`409 COURSE_FULL`):

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
설명: 학생의 강좌 수강취소

경로 파라미터:
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

## 비즈니스 규칙
- 학생 최대 신청 학점: `18`
- 동일 요일에 시간이 1분이라도 겹치면 시간 충돌
- 동일 강좌 중복 신청 금지
- 강좌 정원 초과 금지
- 동시성 제어: `SELECT ... FOR UPDATE` 기반 트랜잭션 처리

## 참고
- OpenAPI(Swagger): `docs/openapi.yaml`
