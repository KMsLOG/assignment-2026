import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.db import db_connection, wait_for_database
from app.seed_data import seed_runtime_data

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


@app.on_event("startup")
def startup() -> None:
    started_at = time.perf_counter()
    wait_for_database(max_wait_seconds=50)
    with db_connection() as conn:
        result = seed_runtime_data(conn)

    app.state.seed_status = {
        "completed": True,
        "seeded": result["seeded"],
        "duration_ms": int((time.perf_counter() - started_at) * 1000),
        "counts": result["counts"],
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "seed": app.state.seed_status,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
