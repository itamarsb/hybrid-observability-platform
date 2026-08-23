"""Tests for application-level OpenTelemetry metrics."""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from hybrid_observability import main as main_module
from hybrid_observability.config import Settings
from hybrid_observability.telemetry import TelemetryRuntime


@pytest.fixture
def metrics_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, InMemoryMetricReader]]:
    """Return an application client with in-memory metric collection."""

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

    metric_reader = InMemoryMetricReader()
    meter_provider = MeterProvider(
        metric_readers=[metric_reader],
    )

    telemetry_runtime = TelemetryRuntime(
        tracer=trace.get_tracer(
            settings.service_name,
            settings.service_version,
        ),
        meter=meter_provider.get_meter(
            settings.service_name,
            settings.service_version,
        ),
        meter_provider=meter_provider,
    )

    def initialize_for_test(
        _application: FastAPI,
        _settings: Settings,
    ) -> TelemetryRuntime:
        return telemetry_runtime

    monkeypatch.setattr(
        main_module,
        "initialize_telemetry",
        initialize_for_test,
    )

    application = main_module.create_app(settings)

    with TestClient(application) as test_client:
        yield test_client, metric_reader


def test_application_metrics_are_recorded(
    metrics_client: tuple[TestClient, InMemoryMetricReader],
) -> None:
    """Controlled scenarios should produce every custom metric."""

    client, metric_reader = metrics_client

    responses = [
        client.get(
            "/api/v1/scenarios/latency",
            params={"delay_ms": 10},
        ),
        client.get(
            "/api/v1/scenarios/latency",
            params={"delay_ms": 101},
        ),
        client.get("/api/v1/scenarios/error"),
        client.get(
            "/api/v1/scenarios/dependency",
            params={"outcome": "success"},
        ),
        client.get(
            "/api/v1/scenarios/dependency",
            params={"outcome": "failure"},
        ),
        client.get(
            "/api/v1/scenarios/dependency",
            params={"outcome": "timeout"},
        ),
    ]

    assert [response.status_code for response in responses] == [
        200,
        400,
        503,
        200,
        502,
        504,
    ]

    metrics_data = metric_reader.get_metrics_data()

    assert metrics_data is not None

    metric_names = {
        metric.name
        for resource_metrics in metrics_data.resource_metrics
        for scope_metrics in resource_metrics.scope_metrics
        for metric in scope_metrics.metrics
    }

    assert {
        "app.scenario.requests",
        "app.scenario.duration",
        "app.dependency.requests",
        "app.dependency.duration",
    }.issubset(metric_names)
