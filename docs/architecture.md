# Architecture

**Language:** **English (US)** | [Português (Brasil)](architecture.pt-BR.md)

## Scope

The Hybrid Observability Platform is a single-node, local-first reference environment
for instrumenting a FastAPI workload, processing its telemetry with OpenTelemetry,
and investigating metrics, logs, and traces in Grafana.

The implemented scope is a six-service Docker Compose stack, provisioned dashboards,
an instrumented workload, application CI, and an end-to-end local validator. An
optional AWS export path is planned but is not part of the current deployment.
The environment favors reproducibility and explicit failure modes over production
scale or continuous availability.

## Implemented components

| Component | Responsibility |
|---|---|
| FastAPI service | Provides deterministic endpoints and controlled HTTP 503, 502, 504, and latency scenarios |
| OpenTelemetry SDK | Produces application metrics and traces and supplies trace context for structured logs |
| OpenTelemetry Collector | Receives OTLP metrics/traces and Fluent Forward application logs, applies configured processors, and routes each signal |
| Prometheus | Scrapes and stores exported metrics for up to 48 hours |
| Loki | Stores local application logs with 24-hour retention |
| Tempo | Stores local traces with 24-hour retention |
| Grafana | Provides provisioned data sources, dashboards, and Loki–Tempo navigation |
| Docker Compose | Manages local services, port bindings, health checks, networks, and volumes |
| Local validator | Starts the stack and independently verifies service health and metrics/logs/traces delivery |

k6 workloads, recording/alerting rules, full-platform CI, and Terraform-managed
AWS integration are roadmap items, not deployed components.

## Current data flow

1. A client or the local validator sends requests to the FastAPI application.
2. FastAPI instrumentation exports metrics and traces over OTLP/gRPC to the Collector.
3. Application JSON logs are written to stdout, forwarded by the Docker Fluentd
   logging driver to the Collector's Fluent Forward receiver, and enriched with
   application resource attributes.
4. The Collector's configured memory limiter and batch processors handle each
   telemetry pipeline. Logs are forwarded to Loki over OTLP/HTTP; traces are
   forwarded to Tempo over OTLP/gRPC; exported metrics are scraped by Prometheus.
5. Grafana queries the backends, with the provisioned Loki derived field and
   Tempo trace-to-logs settings enabling request-specific navigation.

The application configures trace sampling. No Collector tail sampling, payload
redaction processor, or additional exporter queue/retry policy is declared in
the current Collector configuration. Those controls must not be assumed.

## Deployment boundaries

The six services run on a dedicated Compose bridge network. The host-published
service ports are bound to 127.0.0.1 in the checked-in configuration. Prometheus,
Loki, Tempo, and Grafana retain their data in named Docker volumes; the documented
retention windows limit telemetry history but do not eliminate the need for
explicit volume cleanup when data deletion is intended.

AWS credentials are not needed for the implemented local mode. No AWS resources
are provisioned by this repository at present.

## Existing reliability and resource controls

- Container health checks and Compose service dependencies.
- Collector memory limiting and batching.
- Configurable application trace sampling; local Compose currently samples 100%.
- Local Prometheus, Loki, and Tempo retention policies.
- Container CPU and memory limits in Compose.
- A local validator with 16 checks, including a new HTTP 503 route-level metric
  and request-specific Loki/Tempo correlation check. The check has 11 passing
  offline unit tests and a documented successful local 16/16 integration run
  on 2026-11-20.
- Controlled application-side failure and delay scenarios.

Additional hardening (for example, exporter resilience tests, secret-attribute
filtering, load testing, and full-platform security checks) remains to be
implemented and validated. The request-correlation check has been exercised
against the running local stack; automated platform CI remains separate work.

## Investigation scenario

The primary documented workflow generates an intentional HTTP 503, observes
its route/status metrics in Prometheus, finds a structured log in Loki, and
opens the corresponding trace in Tempo using the exact trace ID returned by
the HTTP response. HTTP 502/504 dependency scenarios provide an optional
nested-span investigation.

The current dashboards do not require a metric exemplar to begin this process:
metrics identify the route-level symptom, while the response trace ID and
structured logs identify the individual request. The runbook provides the manual investigation path. The new validator check
also requires the same trace ID in the HTTP response, the structured Loki
error log, and a matching Tempo server span. Prometheus metrics remain
route-level evidence rather than a per-request join. A successful local
full-stack run is documented in the
[HTTP Correlation Validation Record](operations/http-correlation-validation-2026-11-20.md).

See [HTTP Error Investigation Runbook](operations/http-error-investigation.md)
and [Local Stack Validation](operations/local-stack-validation.md).
