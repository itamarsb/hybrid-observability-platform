
"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DeploymentEnvironment = Literal["development", "test", "staging", "production"]
TraceSampler = Literal[
    "always_on",
    "always_off",
    "traceidratio",
    "parentbased_always_on",
    "parentbased_always_off",
    "parentbased_traceidratio",
]


class Settings(BaseSettings):
    """Validated runtime settings for the reference workload."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(
        default="hybrid-observability-api",
        validation_alias="OTEL_SERVICE_NAME",
        min_length=1,
    )
    service_version: str = Field(
        default="0.1.0",
        validation_alias="APP_SERVICE_VERSION",
        min_length=1,
    )
    deployment_environment: DeploymentEnvironment = Field(
        default="development",
        validation_alias="APP_ENVIRONMENT",
    )

    host: str = Field(
        default="127.0.0.1",
        validation_alias="APP_HOST",
        min_length=1,
    )
    port: int = Field(
        default=8000,
        validation_alias="APP_PORT",
        ge=1,
        le=65535,
    )
    log_level: LogLevel = Field(
        default="INFO",
        validation_alias="APP_LOG_LEVEL",
    )

    otel_sdk_disabled: bool = Field(
        default=False,
        validation_alias="OTEL_SDK_DISABLED",
    )
    otlp_endpoint: str = Field(
        default="http://localhost:4317",
        validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT",
        min_length=1,
    )
    otlp_insecure: bool = Field(
        default=True,
        validation_alias="OTEL_EXPORTER_OTLP_INSECURE",
    )
    traces_sampler: TraceSampler = Field(
        default="parentbased_traceidratio",
        validation_alias="OTEL_TRACES_SAMPLER",
    )
    traces_sampler_argument: float = Field(
        default=1.0,
        validation_alias="OTEL_TRACES_SAMPLER_ARG",
        ge=0.0,
        le=1.0,
    )

    maximum_scenario_delay_ms: int = Field(
        default=5000,
        validation_alias="APP_MAXIMUM_SCENARIO_DELAY_MS",
        ge=100,
        le=30000,
    )
    dependency_timeout_seconds: float = Field(
        default=2.0,
        validation_alias="APP_DEPENDENCY_TIMEOUT_SECONDS",
        gt=0.0,
        le=30.0,
    )

    @property
    def telemetry_enabled(self) -> bool:
        """Return whether OpenTelemetry SDK initialization is enabled."""

        return not self.otel_sdk_disabled


@lru_cache
def get_settings() -> Settings:
    """Return a cached and validated settings instance."""

    return Settings()
