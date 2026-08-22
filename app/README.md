# Hybrid Observability API

Instrumented FastAPI workload used by the [Hybrid Observability Platform](../README.md) to generate normal requests, latency, errors, dependency failures, structured logs, and OpenTelemetry traces.

## Requirements

- Python 3.12
- Docker, optional for local container execution
- OpenTelemetry Collector, required only when telemetry export is enabled

## Local setup

From the `app` directory:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install --editable ".[dev]"
