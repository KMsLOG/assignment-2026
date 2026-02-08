"""Application entrypoint and startup lifecycle configuration."""

from contextlib import asynccontextmanager
import os
from threading import Lock
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.courses import router as courses_router
from app.api.enrollments import router as enrollments_router
from app.api.health import router as health_router
from app.api.professors import router as professors_router
from app.api.students import router as students_router
from app.core.exception_handler import register_exception_handlers
from app.core.observability import configure_logging, register_request_middleware
from app.repository.database import SessionLocal, wait_for_database
from app.services.seed_service import seed_runtime_data

_startup_lock = Lock()


def _cors_origins_from_env() -> list[str]:
    """Parse CORS origins from CORS_ALLOW_ORIGINS env."""
    raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:8000,http://localhost:3000")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["http://localhost:8000"]


def _initialize_runtime_state(target_app: FastAPI) -> None:
    """Initialize DB-dependent runtime state once per process."""
    if target_app.state.seed_status.get("completed"):
        return

    with _startup_lock:
        if target_app.state.seed_status.get("completed"):
            return

        started_at = time.perf_counter()
        wait_for_database(max_wait_seconds=50)
        with SessionLocal() as db:
            result = seed_runtime_data(db)

        target_app.state.seed_status = {
            "completed": True,
            "seeded": result["seeded"],
            "duration_ms": int((time.perf_counter() - started_at) * 1000),
            "counts": result["counts"],
        }


@asynccontextmanager
async def lifespan(target_app: FastAPI):
    """Prepare runtime state before serving requests."""
    _initialize_runtime_state(target_app)
    yield


app = FastAPI(lifespan=lifespan)
app.state.seed_status = {
    "completed": False,
    "seeded": False,
    "duration_ms": None,
    "counts": {},
}

origins = _cors_origins_from_env()
allow_credentials = "*" not in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
configure_logging()
register_request_middleware(app)
register_exception_handlers(app)
app.include_router(health_router)
app.include_router(students_router)
app.include_router(professors_router)
app.include_router(courses_router)
app.include_router(enrollments_router)


def startup() -> None:
    """Compatibility helper for test setup."""
    _initialize_runtime_state(app)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
