"""OpenTelemetry tracing configuration for the FastAPI application."""

from dataclasses import dataclass, field
from typing import Final
from uuid import uuid4

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
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
    """Own the tracing resources associated with one application instance."""

    tracer: Tracer
    provider: TracerProvider | None = None
    app: FastAPI | None = None
    _closed: bool = field(default=False, init=False)

    def shutdown(self) -> None:
        """Flush spans, release exporters, and remove instrumentation."""

        if self._closed:
            return

        if self.app is not None:
            FastAPIInstrumentor.uninstrument_app(self.app)

        if self.provider is not None:
            self.provider.force_flush(timeout_millis=5000)
            self.provider.shutdown()

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


def initialize_telemetry(
    app: FastAPI,
    settings: Settings,
) -> TelemetryRuntime:
    """Initialize FastAPI tracing and OTLP export."""

    if not settings.telemetry_enabled:
        logger.info("telemetry_disabled")

        return TelemetryRuntime(
            tracer=trace.get_tracer(
                settings.service_name,
                settings.service_version,
            )
        )

    resource = Resource.create(
        {
            "service.name": settings.service_name,
            "service.version": settings.service_version,
            "service.namespace": "hybrid-observability-platform",
            "service.instance.id": str(uuid4()),
            "deployment.environment.name": settings.deployment_environment,
        }
    )

    provider = TracerProvider(
        resource=resource,
        sampler=_build_sampler(settings),
    )

    exporter = OTLPSpanExporter(
        endpoint=settings.otlp_endpoint,
        insecure=settings.otlp_insecure,
    )

    provider.add_span_processor(BatchSpanProcessor(exporter))

    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        excluded_urls=_HEALTH_CHECK_EXCLUSIONS,
    )

    tracer = provider.get_tracer(
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
        provider=provider,
        app=app,
    )
