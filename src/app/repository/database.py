"""SQLAlchemy engine/session setup and DB readiness checks."""

import os
import time
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


def _int_env(name: str, default: int) -> int:
    """Read an integer environment variable with fallback."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _positive_int_env(name: str, default: int) -> int:
    """Read a positive integer environment variable with fallback."""
    value = _int_env(name, default)
    return value if value > 0 else default


def _non_negative_int_env(name: str, default: int) -> int:
    """Read a non-negative integer environment variable with fallback."""
    value = _int_env(name, default)
    return value if value >= 0 else default


def _float_env(name: str, default: float) -> float:
    """Read a positive float environment variable with fallback."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def database_url() -> str:
    """Build a MySQL SQLAlchemy URL from environment variables."""
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = _int_env("DB_PORT", 3306)
    user = os.getenv("DB_USER", "app")
    password = os.getenv("DB_PASSWORD", "app")
    db_name = os.getenv("DB_NAME", "course_registration")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8mb4"


engine = create_engine(
    database_url(),
    pool_pre_ping=True,
    pool_size=_positive_int_env("DB_POOL_SIZE", 30),
    max_overflow=_non_negative_int_env("DB_MAX_OVERFLOW", 30),
    pool_timeout=_float_env("DB_POOL_TIMEOUT_SECONDS", 5.0),
    pool_recycle=_positive_int_env("DB_POOL_RECYCLE_SECONDS", 1800),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session() -> Generator[Session, None, None]:
    """Yield and clean up a request-scoped database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def wait_for_database(max_wait_seconds: int = 50) -> None:
    """Block until DB connectivity is available or timeout is reached."""
    deadline = time.time() + max_wait_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:  # pragma: no cover
            last_error = exc
            time.sleep(1)

    raise RuntimeError(f"Failed to connect to MySQL within {max_wait_seconds}s: {last_error}")
