# 프로젝트 빌드 방법

1. 템플릿을 기반으로 환경 변수 파일을 생성합니다.

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

2. `.env`에서 민감한 값을 변경합니다.
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`

예시:

```dotenv
MYSQL_ROOT_PASSWORD=change-me-root-password
MYSQL_DATABASE=course_registration
MYSQL_USER=app
MYSQL_PASSWORD=change-me-app-password
APP_DEBUG=false
LOG_LEVEL=INFO
CORS_ALLOW_ORIGINS=http://localhost:8000,http://localhost:3000
ENROLLMENT_LOCK_RETRY_ATTEMPTS=3
ENROLLMENT_LOCK_RETRY_BACKOFF_SECONDS=0.05
```

3. 컨테이너 이미지를 빌드합니다.

```bash
docker compose build
```

# 서버 실행 방법

전체 서비스를 실행합니다.

```bash
docker compose up -d
```

상태 및 로그를 확인합니다.

```bash
docker compose ps
docker compose logs -f app
docker compose logs -f mysql
```

서비스를 중지합니다.

```bash
docker compose down
```

# API 서버 접속 정보

- API 기본 URL: `http://localhost:8000`
- 앱 포트: `8000`
- 헬스체크 엔드포인트: `GET /health`
- OpenAPI 명세: `docs/openapi.yaml`
- 품질/추가평가 대응 문서: `docs/QUALITY.md`
- MySQL 호스트(Compose 내부 네트워크): `mysql:3306`

# 운영 참고 사항

- 요청 추적:
  - 모든 응답에 `X-Request-Id` 헤더가 포함됩니다.
  - 모든 응답에 `X-Process-Time-Ms` 헤더가 포함됩니다.
- 구조화 요청 로그:
  - 메서드, 경로, 상태코드, 처리시간, 요청 ID가 기록됩니다.
  - 로그 레벨은 `LOG_LEVEL`로 제어합니다.
- 에러 응답 보안:
  - 기본 설정에서는 내부 예외 메시지를 외부에 노출하지 않습니다.
  - 로컬 디버깅 시에만 `APP_DEBUG=true`를 사용하세요.
- CORS 설정:
  - `CORS_ALLOW_ORIGINS`에 쉼표(,)로 구분된 허용 출처 목록을 설정합니다.
  - `*`를 포함하면 credential CORS는 자동으로 비활성화됩니다.
- 동시성 재시도 설정:
  - 데드락/락 타임아웃(1213/1205) 시 자동 재시도합니다.
  - `ENROLLMENT_LOCK_RETRY_ATTEMPTS`: 최대 재시도 횟수(기본 `3`)
  - `ENROLLMENT_LOCK_RETRY_BACKOFF_SECONDS`: 선형 백오프 기본값(기본 `0.05`초)
