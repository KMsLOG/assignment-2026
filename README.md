# 프로젝트 빌드 방법

1. 환경 변수 파일 생성 (`.env`)
```bash
cp .env.example .env
```

Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

2. `.env` 파일에서 민감 정보 수정
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`

3. Docker 이미지 빌드 및 컨테이너 준비
```bash
docker compose build
```

# 서버 실행 방법

앱과 DB를 함께 실행:
```bash
docker compose up -d
```

상태 확인:
```bash
docker compose ps
docker compose logs -f app
docker compose logs -f mysql
```

중지:
```powershell
docker compose down
```

# API 서버 접속 정보 (포트 등)

- API Base URL: `http://localhost:8000`
- Port: `8000`
- Health Check: `GET /health`
- OpenAPI(Swagger): `docs/openapi.yaml`
- MySQL Host(컨테이너 내부): `mysql:3306`
