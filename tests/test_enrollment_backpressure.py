from __future__ import annotations

from threading import BoundedSemaphore

from app.api import deps as deps_module


def test_enrollment_backpressure_returns_503_when_slot_unavailable(client, monkeypatch) -> None:
    semaphore = BoundedSemaphore(1)
    assert semaphore.acquire(blocking=False)

    monkeypatch.setattr(deps_module, "ENROLLMENT_MAX_INFLIGHT_REQUESTS", 1)
    monkeypatch.setattr(deps_module, "_enrollment_request_semaphore", semaphore)

    try:
        response = client.post("/api/enrollments", json={"student_id": 1, "course_id": 1})
    finally:
        semaphore.release()

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "ENROLLMENT_REQUEST_LIMIT_REACHED"
    assert body["details"]["max_inflight_requests"] == 1
