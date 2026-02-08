## 1. MySQL 실행 (Docker)

### 1) 컨테이너 기동
```bash
docker compose up -d mysql
```

### 2) 상태 확인
```bash
docker compose ps
docker compose logs -f mysql
```

## 2. 서버 실행

`PYTHONPATH=src` 환경에서 FastAPI 서버를 실행합니다.

Windows PowerShell:
```powershell
$env:PYTHONPATH="src"
.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 3. 프로젝트 구조

```text
src/app/
├── api/          # Controller layer (REST endpoints)
├── services/     # Business logic
├── repository/   # SQLAlchemy data access
├── domain/       # DTO / response schemas
├── core/         # Global exception handler
└── main.py       # App bootstrap
```

## 4. 데이터 생성 방식

- 스키마 생성: `infra/mysql/init/01_schema.sql` (DB 초기화 시 1회)
- 데이터 생성: **애플리케이션 startup 시 Python 로직으로 동적 생성**
  - 파일: `src/app/services/seed_service.py`
  - `GET /health`가 `200` 응답하기 전에 데이터 생성 완료
  - 최소 데이터 보장:
    - 학과 12개
    - 교수 120명
    - 강좌 600개
    - 학생 10,000명

## 5. 데이터 재생성

DB 볼륨 초기화:
```bash
docker compose down -v
docker compose up -d mysql
```

서버를 다시 시작하면 startup 시더가 다시 동작합니다.

## 6. 데이터 개수 확인
```bash
docker exec -it assignment-2026-mysql \
  mysql --default-character-set=utf8mb4 -h 127.0.0.1 -uapp -papp -D course_registration \
  -e "SELECT 'departments' t, COUNT(*) c FROM departments
      UNION ALL SELECT 'professors', COUNT(*) FROM professors
      UNION ALL SELECT 'courses', COUNT(*) FROM courses
      UNION ALL SELECT 'students', COUNT(*) FROM students;"
```

## 7. API 문서

- OpenAPI(Swagger): `docs/openapi.yaml`
- 문서 안내: `docs/API.md`
- 요구사항/설계 결정: `docs/REQUIREMENTS.md`
