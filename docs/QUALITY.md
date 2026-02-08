# 품질 및 추가 평가 대응 노트

이 문서는 최소 API 기능 외에, 추가 평가 요소를 고려해 반영한 비기능 개선 사항을 정리합니다.

## 1. 운영 안정성

- FastAPI의 deprecated startup 이벤트를 제거하고 lifespan 초기화로 전환했습니다.
- 동일 프로세스에서 중복 seed 작업이 발생하지 않도록 초기화 구간에 락을 적용했습니다.
- 앱 프로세스 관점에서 런타임 초기화가 멱등적으로 동작하도록 구성했습니다.

관련 파일:
- `src/app/main.py`

## 2. 관측 가능성

- 요청 추적:
  - `X-Request-Id`를 모든 응답에 전파합니다.
  - `X-Process-Time-Ms`를 모든 응답에 포함합니다.
- 구조화 접근 로그:
  - request id, method, path, status code, duration, client ip를 기록합니다.
- 로그 레벨:
  - `LOG_LEVEL` 환경변수로 제어합니다.

관련 파일:
- `src/app/core/observability.py`
- `src/app/main.py`

검증:
- `tests/test_catalog_api.py`

## 3. 보안 기본기

- 기본 설정에서 내부 서버 에러의 원본 예외 메시지를 외부에 노출하지 않습니다.
- 로컬 디버깅 시에만 `APP_DEBUG=true`를 사용하도록 분리했습니다.
- 모든 에러 응답 details에 `request_id`를 포함해 추적성을 확보했습니다.
- CORS 출처를 `CORS_ALLOW_ORIGINS` 환경변수 기반 allowlist로 관리합니다.
- 와일드카드(`*`)를 사용할 경우 credential CORS는 자동 비활성화됩니다.

관련 파일:
- `src/app/core/exception_handler.py`
- `src/app/main.py`
- `.env.example`

검증:
- `tests/test_error_handling.py`

## 4. 테스트 재현성

- 테스트 실행 시 `.env` 또는 `.env.example`을 자동 로딩합니다.
- 로컬/CI에서 DB 연결 환경값이 없을 때를 대비해 기본값을 주입합니다.

관련 파일:
- `tests/conftest.py`

## 5. 문서화

- 런타임 설정 변수와 운영 시 참고할 항목을 `README.md`에 반영했습니다.
- 본 문서를 통해 비기능 의사결정과 근거를 명시했습니다.
