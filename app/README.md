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
```

Activate the virtual environment.

On Linux or macOS:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## Run locally

For local execution without an OpenTelemetry Collector, disable telemetry export.

On Linux or macOS:

```bash
export OTEL_SDK_DISABLED=true
uvicorn hybrid_observability.main:app --host 127.0.0.1 --port 8000
```

On Windows PowerShell:

```powershell
$env:OTEL_SDK_DISABLED = "true"
uvicorn hybrid_observability.main:app --host 127.0.0.1 --port 8000
```

The API will be available at:

- API base URL: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI specification: `http://127.0.0.1:8000/openapi.json`

## Endpoints

| Method | Endpoint | Purpose | Expected status |
|:---:|---|---|:---:|
| `GET` | `/health/live` | Confirms that the application process is running | `200` |
| `GET` | `/health/ready` | Confirms that the application is ready to receive requests | `200` |
| `GET` | `/api/v1/items/{item_id}` | Returns a deterministic reference item | `200` |
| `GET` | `/api/v1/scenarios/latency?delay_ms=250` | Introduces a controlled response delay | `200` |
| `GET` | `/api/v1/scenarios/error` | Generates a controlled service failure | `503` |
| `GET` | `/api/v1/scenarios/dependency?outcome=success` | Simulates a successful dependency call | `200` |
| `GET` | `/api/v1/scenarios/dependency?outcome=failure` | Simulates an unavailable dependency | `502` |
| `GET` | `/api/v1/scenarios/dependency?outcome=timeout` | Simulates a dependency timeout | `504` |

Example requests:

```bash
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
curl http://127.0.0.1:8000/api/v1/items/42
curl "http://127.0.0.1:8000/api/v1/scenarios/latency?delay_ms=500"
curl http://127.0.0.1:8000/api/v1/scenarios/error
curl "http://127.0.0.1:8000/api/v1/scenarios/dependency?outcome=success"
curl "http://127.0.0.1:8000/api/v1/scenarios/dependency?outcome=failure"
curl "http://127.0.0.1:8000/api/v1/scenarios/dependency?outcome=timeout"
```

The scenario endpoints intentionally produce observable success, latency, client validation errors, service errors, dependency failures, and timeouts.

## Quality checks

Run all commands from the `app` directory after installing the development dependencies.

Run the automated tests with coverage:

```bash
pytest
```

Run the linter:

```bash
ruff check src tests
```

Verify formatting:

```bash
ruff format --check src tests
```

Run static type checking:

```bash
mypy src tests
```

Apply automatic formatting when necessary:

```bash
ruff format src tests
```

The test configuration requires at least 85% statement coverage and enables branch coverage.

## Container execution

Build the container image from the `app` directory:

```bash
docker build --tag hybrid-observability-api:local .
```

Run the container without telemetry export:

```bash
docker run --rm \
  --name hybrid-observability-api \
  --publish 8000:8000 \
  --env OTEL_SDK_DISABLED=true \
  hybrid-observability-api:local
```

On Windows PowerShell, the same container can be started with:

```powershell
docker run --rm `
  --name hybrid-observability-api `
  --publish 8000:8000 `
  --env OTEL_SDK_DISABLED=true `
  hybrid-observability-api:local
```

Verify the running container:

```bash
curl http://127.0.0.1:8000/health/live
```

The image uses a multi-stage build, installs the packaged application into a dedicated virtual environment, runs as the unprivileged user `appuser`, and includes a health check for `/health/live`.

## Configuration

Configuration is loaded from environment variables. A local `.env` file may also be used and must not be committed when it contains environment-specific or sensitive values.

| Variable | Default | Description |
|---|---|---|
| `OTEL_SERVICE_NAME` | `hybrid-observability-api` | OpenTelemetry service name |
| `APP_SERVICE_VERSION` | `0.1.0` | Application and API version |
| `APP_ENVIRONMENT` | `development` | Deployment environment: `development`, `test`, `staging`, or `production` |
| `APP_HOST` | `127.0.0.1` | Local application bind address |
| `APP_PORT` | `8000` | Application listening port |
| `APP_LOG_LEVEL` | `INFO` | Structured logging level |
| `OTEL_SDK_DISABLED` | `false` | Disables OpenTelemetry SDK initialization when set to `true` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP gRPC Collector endpoint |
| `OTEL_EXPORTER_OTLP_INSECURE` | `true` | Enables an insecure OTLP gRPC connection |
| `OTEL_TRACES_SAMPLER` | `parentbased_traceidratio` | OpenTelemetry trace sampler |
| `OTEL_TRACES_SAMPLER_ARG` | `1.0` | Trace sampling ratio between `0.0` and `1.0` |
| `APP_MAXIMUM_SCENARIO_DELAY_MS` | `5000` | Maximum permitted latency scenario delay |
| `APP_DEPENDENCY_TIMEOUT_SECONDS` | `2.0` | Timeout applied to the simulated dependency |

Example configuration for local execution with telemetry enabled:

```bash
export OTEL_SDK_DISABLED=false
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_INSECURE=true
uvicorn hybrid_observability.main:app --host 127.0.0.1 --port 8000
```

Docker Compose will later configure the Collector endpoint as `http://otel-collector:4317`.
