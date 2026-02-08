# Quality and Extra Evaluation Notes

This document summarizes non-functional improvements that were added beyond the minimum API feature list.

## 1. Operational Stability

- FastAPI startup event deprecation was removed by switching to lifespan initialization.
- Startup initialization is guarded by a lock to avoid duplicate seeding work in the same process.
- Runtime initialization is idempotent at app-process level.

Related files:
- `src/app/main.py`

## 2. Observability

- Request tracing:
  - `X-Request-Id` is propagated to every response.
  - `X-Process-Time-Ms` is included in every response.
- Structured access logs include:
  - request id, method, path, status code, duration, client ip.
- Log level is configurable by `LOG_LEVEL`.

Related files:
- `src/app/core/observability.py`
- `src/app/main.py`

Validation:
- `tests/test_catalog_api.py`

## 3. Security Baseline

- Internal server errors do not expose raw exception messages by default.
- `APP_DEBUG=true` can be enabled for local debugging only.
- `request_id` is included in all error payloads for traceability.
- CORS origins are environment-driven allowlist via `CORS_ALLOW_ORIGINS`.
- When wildcard `*` is used, credentialed CORS is disabled automatically.

Related files:
- `src/app/core/exception_handler.py`
- `src/app/main.py`
- `.env.example`

Validation:
- `tests/test_error_handling.py`

## 4. Test Reproducibility

- Tests automatically load `.env` or `.env.example`.
- DB connection env values are populated with sane defaults for local/CI execution.

Related files:
- `tests/conftest.py`

## 5. Documentation

- Runtime configuration variables are documented in `README.md`.
- This quality checklist is provided to make non-functional decisions explicit.
