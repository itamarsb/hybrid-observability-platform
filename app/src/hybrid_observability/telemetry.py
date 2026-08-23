"""OpenTelemetry tracing and metrics configuration for the FastAPI application."""

from dataclasses import dataclass, field
from typing import Final
from uuid import uuid4

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.metrics import Meter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    ParentBased,
    Sampler,
    TraceIdRatioBased,
)
from opentelemetry.trace import Tracer

from hybrid_observability.config import Settings
from hybrid_observability.logging import get_logger

logger = get_logger(__name__)

_HEALTH_CHECK_EXCLUSIONS: Final = "health/live,health/ready"


@dataclass(slots=True)
class TelemetryRuntime:
    """Own the telemetry resources associated with one application instance."""

    tracer: Tracer
    meter: Meter
    tracer_provider: TracerProvider | None = None
    meter_provider: MeterProvider | None = None
    app: FastAPI | None = None
    _closed: bool = field(default=False, init=False)

    def shutdown(self) -> None:
        """Flush telemetry, release exporters, and remove instrumentation."""

        if self._closed:
            return

        if self.app is not None:
            FastAPIInstrumentor.uninstrument_app(self.app)

        if self.meter_provider is not None:
            self.meter_provider.force_flush(timeout_millis=5000)
            self.meter_provider.shutdown(timeout_millis=5000)

        if self.tracer_provider is not None:
            self.tracer_provider.force_flush(timeout_millis=5000)
            self.tracer_provider.shutdown()

        self._closed = True
        logger.info("telemetry_shutdown_completed")


def _build_sampler(settings: Settings) -> Sampler:
    """Build the configured trace sampler."""

    samplers: dict[str, Sampler] = {
        "always_on": ALWAYS_ON,
        "always_off": ALWAYS_OFF,
        "traceidratio": TraceIdRatioBased(settings.traces_sampler_argument),
        "parentbased_always_on": ParentBased(root=ALWAYS_ON),
        "parentbased_always_off": ParentBased(root=ALWAYS_OFF),
        "parentbased_traceidratio": ParentBased(
            root=TraceIdRatioBased(settings.traces_sampler_argument)
        ),
    }

    return samplers[settings.traces_sampler]


def _build_resource(settings: Settings) -> Resource:
    """Build shared resource attributes for all telemetry signals."""

    return Resource.create(
        {
            "service.name": settings.service_name,
            "service.version": settings.service_version,
            "service.namespace": "hybrid-observability-platform",
            "service.instance.id": str(uuid4()),
            "deployment.environment.name": settings.deployment_environment,
        }
    )


def initialize_telemetry(
    app: FastAPI,
    settings: Settings,
) -> TelemetryRuntime:
    """Initialize FastAPI tracing and metrics with OTLP export."""

    if not settings.telemetry_enabled:
        logger.info("telemetry_disabled")

        return TelemetryRuntime(
            tracer=trace.get_tracer(
                settings.service_name,
                settings.service_version,
            ),
            meter=metrics.get_meter(
                settings.service_name,
                settings.service_version,
            ),
        )

    resource = _build_resource(settings)

    tracer_provider = TracerProvider(
        resource=resource,
        sampler=_build_sampler(settings),
    )

    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=settings.otlp_endpoint,
                insecure=settings.otlp_insecure,
            )
        )
    )

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=settings.otlp_endpoint,
            insecure=settings.otlp_insecure,
        )
    )

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )

    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
        excluded_urls=_HEALTH_CHECK_EXCLUSIONS,
    )

    tracer = tracer_provider.get_tracer(
        settings.service_name,
        settings.service_version,
    )

    meter = meter_provider.get_meter(
        settings.service_name,
        settings.service_version,
    )

    logger.info(
        "telemetry_initialized",
        extra={
            "otlp_endpoint": settings.otlp_endpoint,
            "traces_sampler": settings.traces_sampler,
            "traces_sampler_argument": settings.traces_sampler_argument,
        },
    )

    return TelemetryRuntime(
        tracer=tracer,
        meter=meter,
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
        app=app,
    )
