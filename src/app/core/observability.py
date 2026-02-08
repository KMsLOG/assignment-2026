"""Observability utilities for request tracing and structured logging."""

from __future__ import annotations

import json
import logging
import os
import time
from uuid import uuid4

from fastapi import FastAPI, Request


REQUEST_ID_HEADER = "X-Request-Id"
PROCESS_TIME_HEADER = "X-Process-Time-Ms"

_request_logger = logging.getLogger("app.request")


def configure_logging() -> None:
    """Configure process-wide logging with env-driven log level."""
    raw_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    level = getattr(logging, raw_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def request_id_from_request(request: Request) -> str | None:
    """Return request id from request state or header."""
    state_request_id = getattr(request.state, "request_id", None)
    if isinstance(state_request_id, str) and state_request_id:
        return state_request_id

    header_request_id = request.headers.get(REQUEST_ID_HEADER)
    if isinstance(header_request_id, str) and header_request_id:
        return header_request_id
    return None


def register_request_middleware(app: FastAPI) -> None:
    """Attach request id propagation and access logging middleware."""

    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[PROCESS_TIME_HEADER] = str(elapsed_ms)

        payload = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": elapsed_ms,
            "client_ip": request.client.host if request.client else None,
        }
        _request_logger.info(json.dumps(payload, ensure_ascii=False))
        return response
