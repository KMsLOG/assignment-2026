"""Global FastAPI exception handler registration."""

import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError

from app.core.exceptions import AppException
from app.core.observability import request_id_from_request

_logger = logging.getLogger("app.exception")


def _debug_enabled() -> bool:
    raw = os.getenv("APP_DEBUG", "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _with_request_id(request: Request, details: dict[str, object] | None = None) -> dict[str, object]:
    merged = dict(details or {})
    request_id = request_id_from_request(request)
    if request_id is not None:
        merged.setdefault("request_id", request_id)
    return merged


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers for domain, validation, and unexpected exceptions."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Translate AppException into a structured JSON error response."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "details": _with_request_id(request, exc.details),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Normalize FastAPI validation errors into a project error contract."""
        return JSONResponse(
            status_code=400,
            content={
                "code": "INVALID_REQUEST",
                "message": "Request validation failed.",
                "details": _with_request_id(request, {"errors": exc.errors()}),
            },
        )

    @app.exception_handler(SQLAlchemyTimeoutError)
    async def db_pool_timeout_handler(request: Request, exc: SQLAlchemyTimeoutError) -> JSONResponse:
        """Return a retryable 503 when DB connection pool is saturated."""
        details = _with_request_id(request)
        _logger.warning(
            "Database pool timeout",
            exc_info=True,
            extra={
                "request_id": details.get("request_id"),
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=503,
            content={
                "code": "DB_CONNECTION_POOL_EXHAUSTED",
                "message": "Database connection pool is busy. Please retry shortly.",
                "details": details,
            },
        )

    @app.exception_handler(Exception)
    async def unknown_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch unhandled exceptions and return a generic server error."""
        details = _with_request_id(request)
        _logger.exception(
            "Unhandled exception",
            extra={
                "request_id": details.get("request_id"),
                "path": request.url.path,
                "method": request.method,
            },
        )
        if _debug_enabled():
            details["error"] = str(exc)

        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected server error.",
                "details": details,
            },
        )
