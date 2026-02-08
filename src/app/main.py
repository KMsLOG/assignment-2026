"""Application entrypoint and startup lifecycle configuration."""

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
from app.repository.database import SessionLocal, wait_for_database
from app.services.seed_service import seed_runtime_data

app = FastAPI()
app.state.seed_status = {
    "completed": False,
    "seeded": False,
    "duration_ms": None,
    "counts": {},
}

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(health_router)
app.include_router(students_router)
app.include_router(professors_router)
app.include_router(courses_router)
app.include_router(enrollments_router)


@app.on_event("startup")
def startup() -> None:
    """Wait for DB readiness and seed runtime data before serving traffic."""
    started_at = time.perf_counter()
    wait_for_database(max_wait_seconds=50)
    with SessionLocal() as db:
        result = seed_runtime_data(db)

    app.state.seed_status = {
        "completed": True,
        "seeded": result["seeded"],
        "duration_ms": int((time.perf_counter() - started_at) * 1000),
        "counts": result["counts"],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
