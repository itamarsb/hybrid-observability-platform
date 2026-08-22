"""Tests for application creation and health-check endpoints."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from hybrid_observability.config import Settings
from hybrid_observability.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Return isolated settings suitable for automated tests."""

    return Settings.model_validate(
        {
            "OTEL_SERVICE_NAME": "hybrid-observability-api-test",
            "APP_SERVICE_VERSION": "0.1.0-test",
            "APP_ENVIRONMENT": "test",
            "APP_LOG_LEVEL": "ERROR",
            "OTEL_SDK_DISABLED": True,
        }
    )


@pytest.fixture
def client(test_settings: Settings) -> Iterator[TestClient]:
    """Return a test client with application lifespan enabled."""

    application = create_app(test_settings)

    with TestClient(application) as test_client:
        yield test_client


def test_application_metadata(test_settings: Settings) -> None:
    """Application factory should apply configured API metadata."""

    application = create_app(test_settings)

    assert application.title == "Hybrid Observability API"
    assert application.version == "0.1.0-test"
    assert application.state.settings is test_settings
    assert application.state.telemetry is not None


def test_liveness_endpoint(client: TestClient) -> None:
    """Liveness should confirm that the process is operational."""

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "service": "hybrid-observability-api-test",
        "version": "0.1.0-test",
        "environment": "test",
        "telemetry_enabled": False,
    }


def test_readiness_endpoint(client: TestClient) -> None:
    """Readiness should not depend on an available telemetry Collector."""

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "hybrid-observability-api-test",
        "version": "0.1.0-test",
        "environment": "test",
        "telemetry_enabled": False,
    }


@pytest.mark.parametrize(
    "endpoint",
    [
        "/health/live",
        "/health/ready",
    ],
)
def test_health_responses_are_json(
    client: TestClient,
    endpoint: str,
) -> None:
    """Health endpoints should return the documented content type."""

    response = client.get(endpoint)

    assert response.headers["content-type"] == "application/json"
