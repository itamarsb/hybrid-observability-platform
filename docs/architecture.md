# Architecture

## Scope

The Hybrid Observability Platform is a single-node reference environment for instrumenting a FastAPI workload, processing its telemetry through OpenTelemetry, and investigating metrics, logs, and traces in Grafana. An optional path validates selected telemetry in AWS.

The first release optimizes for reproducibility, understandable failure modes, and safe teardown rather than scale or continuous availability.

## Components

| Component | Responsibility |
|---|---|
| FastAPI service | Provides instrumented endpoints and controlled error/latency scenarios |
| OpenTelemetry SDK | Produces application metrics, logs, traces, and resource attributes |
| OpenTelemetry Collector | Receives OTLP, processes telemetry, and routes it to enabled exporters |
| Prometheus | Stores and queries local metrics |
| Loki | Stores and queries local logs |
| Tempo | Stores and queries local traces |
| Grafana | Provisions data sources, dashboards, alerts, and cross-signal navigation |
| k6 | Generates bounded, repeatable workloads |
| Terraform | Creates and removes resources required by hybrid mode |

## Data flow

1. k6 sends a controlled workload to the FastAPI service.
2. Application instrumentation exports OTLP telemetry to the Collector.
3. Collector processors batch data, protect memory, remove sensitive attributes, and apply sampling or filtering.
4. Local exporters route metrics, logs, and traces to Prometheus, Loki, and Tempo.
5. Grafana queries those backends and links related signals through shared attributes such as service name and trace ID.
6. When hybrid mode is explicitly enabled, approved telemetry is also sent to CloudWatch and X-Ray.

## Deployment boundaries

All local services run in a dedicated Compose network. Only ports required for development access are published to the host, bound to localhost by default. Backend data uses named project volumes and is intentionally disposable.

AWS credentials remain outside containers and version control. Hybrid resources must be tagged and managed by Terraform. The local path continues to function if AWS export is unavailable.

## Reliability and resource controls

- health checks and dependency readiness for every service;
- Collector memory limiter, batching, queueing, and retry policies;
- bounded metric labels and trace sampling;
- explicit backend retention and container resource limits;
- deterministic workload duration and rate;
- observable Collector failures and exporter drops;
- project-scoped cleanup with post-cleanup verification.

## Key investigation scenario

The initial end-to-end scenario will introduce controlled latency and errors in the API. A dashboard identifies elevated latency or error rate, an exemplar links the metric to a trace, and the trace ID retrieves correlated application logs. The same scenario is repeated with an unavailable exporter to prove that the local pipeline remains operational.
