from fastapi.testclient import TestClient

from app.main import create_app


def test_health_reports_process_liveness() -> None:
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_dependency_status() -> None:
    app = create_app(lambda: {"database": True, "redis": True})

    response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "dependencies": {"database": True, "redis": True}}


def test_ready_returns_503_when_a_dependency_is_unavailable() -> None:
    app = create_app(lambda: {"database": True, "redis": False})

    response = TestClient(app).get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_request_id_is_echoed() -> None:
    response = TestClient(create_app()).get("/health", headers={"X-Request-ID": "test-request-id"})

    assert response.headers["X-Request-ID"] == "test-request-id"
