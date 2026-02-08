# Project Build

1. Create an environment file from the template:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

2. Update sensitive values in `.env`:
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`

Example:

```dotenv
MYSQL_ROOT_PASSWORD=change-me-root-password
MYSQL_DATABASE=course_registration
MYSQL_USER=app
MYSQL_PASSWORD=change-me-app-password
APP_DEBUG=false
LOG_LEVEL=INFO
CORS_ALLOW_ORIGINS=http://localhost:8000,http://localhost:3000
```

3. Build containers:

```bash
docker compose build
```

# Server Run

Start all services:

```bash
docker compose up -d
```

Check status and logs:

```bash
docker compose ps
docker compose logs -f app
docker compose logs -f mysql
```

Stop services:

```bash
docker compose down
```

# API Access

- API base URL: `http://localhost:8000`
- App port: `8000`
- Health endpoint: `GET /health`
- OpenAPI spec: `docs/openapi.yaml`
- Quality notes: `docs/QUALITY.md`
- MySQL host (inside compose network): `mysql:3306`

# Operational Notes

- Request tracing:
  - Every response includes `X-Request-Id`
  - Every response includes `X-Process-Time-Ms`
- Structured request logs:
  - Method, path, status, duration, request id are logged
  - Log level is controlled by `LOG_LEVEL`
- Error response hardening:
  - By default, internal exception messages are not exposed
  - Set `APP_DEBUG=true` only for local debugging
- CORS configuration:
  - Use `CORS_ALLOW_ORIGINS` as a comma-separated allowlist
  - If `*` is included, credentialed CORS is disabled automatically
