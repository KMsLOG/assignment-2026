import os
import time
from contextlib import contextmanager

import pymysql
from pymysql.connections import Connection


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def db_settings() -> dict[str, object]:
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": _int_env("DB_PORT", 3306),
        "user": os.getenv("DB_USER", "app"),
        "password": os.getenv("DB_PASSWORD", "app"),
        "database": os.getenv("DB_NAME", "course_registration"),
        "charset": "utf8mb4",
        "autocommit": False,
        "connect_timeout": _int_env("DB_CONNECT_TIMEOUT_SECONDS", 5),
    }


@contextmanager
def db_connection() -> Connection:
    conn = pymysql.connect(**db_settings())
    try:
        yield conn
    finally:
        conn.close()


def wait_for_database(max_wait_seconds: int = 50) -> None:
    deadline = time.time() + max_wait_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            with db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return
        except Exception as exc:  # pragma: no cover
            last_error = exc
            time.sleep(1)

    raise RuntimeError(f"Failed to connect to MySQL within {max_wait_seconds}s: {last_error}")
