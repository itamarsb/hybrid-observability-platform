"""Tests for normal requests and controlled observability scenarios."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from hybrid_observability.config import Settings
from hybrid_observability.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Return an isolated application client for scenario tests."""

    settings = Settings.model_validate(
        {
            "OTEL_SERVICE_NAME": "hybrid-observability-api-test",
            "APP_SERVICE_VERSION": "0.1.0-test",
            "APP_ENVIRONMENT": "test",
            "APP_LOG_LEVEL": "ERROR",
            "OTEL_SDK_DISABLED": True,
            "APP_MAXIMUM_SCENARIO_DELAY_MS": 100,
            "APP_DEPENDENCY_TIMEOUT_SECONDS": 0.01,
        }
    )

    application = create_app(settings)

    with TestClient(application) as test_client:
        yield test_client


def test_get_item(client: TestClient) -> None:
    """A valid item identifier should return a deterministic item."""

    response = client.get("/api/v1/items/42")

    assert response.status_code == 200
    assert response.json() == {
        "item_id": 42,
        "name": "reference-item-42",
        "status": "available",
    }


@pytest.mark.parametrize(
    "item_id",
    [
        "0",
        "-1",
        "invalid",
    ],
)
def test_get_item_rejects_invalid_identifier(
    client: TestClient,
    item_id: str,
) -> None:
    """Invalid item identifiers should be rejected by request validation."""

    response = client.get(f"/api/v1/items/{item_id}")

    assert response.status_code == 422
    assert "detail" in response.json()


def test_latency_scenario(client: TestClient) -> None:
    """A permitted delay should complete successfully."""

    response = client.get(
        "/api/v1/scenarios/latency",
        params={"delay_ms": 10},
    )

    assert response.status_code == 200
    assert response.json() == {
        "scenario": "latency",
        "outcome": "success",
        "duration_ms": 10,
    }


def test_latency_scenario_rejects_excessive_delay(
    client: TestClient,
) -> None:
    """A delay above the configured limit should be rejected."""

    response = client.get(
        "/api/v1/scenarios/latency",
        params={"delay_ms": 101},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": "scenario_delay_exceeded",
        "message": ("Requested delay exceeds the configured maximum of 100 ms."),
        "trace_id": None,
    }


def test_latency_scenario_rejects_negative_delay(
    client: TestClient,
) -> None:
    """A negative delay should fail FastAPI request validation."""

    response = client.get(
        "/api/v1/scenarios/latency",
        params={"delay_ms": -1},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_error_scenario(client: TestClient) -> None:
    """The controlled error scenario should return HTTP 503."""

    response = client.get("/api/v1/scenarios/error")

    assert response.status_code == 503
    assert response.json() == {
        "error": "controlled_service_failure",
        "message": "A controlled service failure was generated.",
        "trace_id": None,
    }


def test_dependency_success(client: TestClient) -> None:
    """A successful simulated dependency should return HTTP 200."""

    response = client.get(
        "/api/v1/scenarios/dependency",
        params={"outcome": "success"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "scenario": "dependency",
        "outcome": "success",
        "duration_ms": None,
    }


def test_dependency_failure(client: TestClient) -> None:
    """A simulated connection failure should return HTTP 502."""

    response = client.get(
        "/api/v1/scenarios/dependency",
        params={"outcome": "failure"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": "dependency_unavailable",
        "message": "The simulated dependency is unavailable.",
        "trace_id": None,
    }


def test_dependency_timeout(client: TestClient) -> None:
    """A simulated dependency timeout should return HTTP 504."""

    response = client.get(
        "/api/v1/scenarios/dependency",
        params={"outcome": "timeout"},
    )

    assert response.status_code == 504
    assert response.json() == {
        "error": "dependency_timeout",
        "message": "The simulated dependency exceeded its timeout.",
        "trace_id": None,
    }


def test_dependency_rejects_unknown_outcome(
    client: TestClient,
) -> None:
    """An unsupported dependency outcome should fail validation."""

    response = client.get(
        "/api/v1/scenarios/dependency",
        params={"outcome": "unknown"},
    )

    assert response.status_code == 422
    assert "detail" in response.json()
