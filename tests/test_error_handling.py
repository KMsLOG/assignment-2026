from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exception_handler import register_exception_handlers


def _build_error_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> dict[str, str]:
        raise RuntimeError("boom")

    return app


def test_internal_error_hides_raw_exception_by_default(monkeypatch) -> None:
    monkeypatch.delenv("APP_DEBUG", raising=False)
    app = _build_error_app()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom", headers={"X-Request-Id": "err-default"})

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_SERVER_ERROR"
    assert body["details"]["request_id"] == "err-default"
    assert "error" not in body["details"]


def test_internal_error_includes_raw_exception_in_debug(monkeypatch) -> None:
    monkeypatch.setenv("APP_DEBUG", "true")
    app = _build_error_app()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom", headers={"X-Request-Id": "err-debug"})

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_SERVER_ERROR"
    assert body["details"]["request_id"] == "err-debug"
    assert "boom" in body["details"]["error"]
