# Local Stack Validation

## Purpose

The local stack validator provides a reproducible end-to-end check of the Hybrid
Observability Platform. It verifies not only that the containers are running, but also
that the application can emit metrics, logs, and traces and that each signal reaches its
intended local backend.

The validator is designed to run consistently on Windows, Linux, macOS, and GitHub
Actions. It uses only the Python standard library and the Docker CLI.

## Prerequisites

- Python 3.12 or later;
- Docker Engine or Docker Desktop with Docker Compose v2;
- the Docker daemon running;
- local ports `3000`, `3100`, `3200`, `4317`, `4318`, `8000`, `8888`, `8889`, and
  `9090` available;
- permission to build images and start containers.

Run all commands from the repository root.

## Run the validation

Windows PowerShell:

```powershell
python .\scripts\validate-local-stack.py
```

Linux or macOS:

```bash
python3 ./scripts/validate-local-stack.py
```

The telemetry backends are eventually consistent. By default, the validator waits up to
60 seconds for generated telemetry to become queryable. Increase that interval on slower
workstations or CI runners:

```powershell
python .\scripts\validate-local-stack.py --telemetry-timeout 120
```

## Validation sequence

The checks run in a fixed order and stop at the first failure:

1. validate the resolved Docker Compose configuration;
2. build and start the local stack with Docker Compose;
3. confirm that all six Compose services are running and healthy;
4. query the OpenTelemetry Collector health endpoint;
5. query the Prometheus, Loki, Tempo, and Grafana health endpoints;
6. query the application liveness and readiness endpoints;
7. confirm that the Prometheus scrape targets are up;
8. generate deterministic application, latency, and controlled-error requests;
9. confirm that custom application metrics reached Prometheus;
10. confirm that structured application logs reached Loki;
11. confirm that application traces reached Tempo.

The controlled error generated during validation is intentional. An HTTP `503` response
from that scenario is expected and is used to validate error telemetry.

## Successful result

A successful run ends with:

```text
Validation completed successfully: 15/15 checks passed.
The stack remains running and all named volumes are preserved.
```

Exit code `0` means that every check passed. Exit code `1` means that a prerequisite was
missing or a validation check failed.

The validator does not stop the platform or remove telemetry after completion. This makes
the generated signals available for investigation in Grafana.

## Inspect the running platform

After a successful run, the main local interfaces are:

| Component | URL |
|---|---|
| Application API documentation | <http://127.0.0.1:8000/docs> |
| Grafana | <http://127.0.0.1:3000> |
| Prometheus | <http://127.0.0.1:9090> |

Grafana uses `admin` / `admin` by default in local mode unless
`GRAFANA_ADMIN_USER` and `GRAFANA_ADMIN_PASSWORD` are set in the environment.

## Stop the stack safely

Stop and remove the project containers and network while preserving all named volumes:

```powershell
docker compose down
```

Do not add `--volumes` or `-v` when the telemetry databases and Grafana configuration
must be preserved. Removing the named volumes permanently deletes the locally stored
Prometheus metrics, Loki logs, Tempo traces, and Grafana state.

## Troubleshooting

### Docker is not available

Confirm that Docker Desktop or Docker Engine is running:

```powershell
docker version
docker compose version
```

### A container is unhealthy

Inspect service state and recent logs:

```powershell
docker compose ps
docker compose logs --tail 100 <service-name>
```

Replace `<service-name>` with `app`, `otel-collector`, `prometheus`, `loki`, `tempo`, or
`grafana`.

### Telemetry is not found before the timeout

Run the validator with a longer telemetry timeout:

```powershell
python .\scripts\validate-local-stack.py --telemetry-timeout 120
```

If the failure remains, inspect the application and Collector logs:

```powershell
docker compose logs --tail 100 app otel-collector
```

### A local port is already in use

Stop the conflicting process or stack before retrying. On Windows, identify the process
using a port with:

```powershell
Get-NetTCPConnection -LocalPort <port-number>
```

