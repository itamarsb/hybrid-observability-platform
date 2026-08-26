# Application Observability

## Purpose

The `Application Overview` dashboard provides a request-centered view of the instrumented
FastAPI service. It combines RED-style service indicators, controlled scenario metrics,
dependency behavior, and structured application logs in a single provisioned dashboard.

The dashboard definition is version controlled at:

```text
observability/grafana/dashboards/application-overview.json
```

## Prerequisites

- the local platform is running and healthy;
- the Prometheus, Loki, and Tempo data sources are provisioned;
- application traffic exists within the selected dashboard time range.

Run the end-to-end validator before opening the dashboard:

```powershell
python .\scripts\validate-local-stack.py
```

Open Grafana at <http://127.0.0.1:3000> and select:

```text
Dashboards > Hybrid Observability Platform > Application Overview
```

## Dashboard panels

| Panel | Meaning |
|---|---|
| Request Rate | HTTP requests per second for the selected routes |
| Error Rate | Percentage of requests returning an HTTP 5xx status |
| Latency P95 | Duration below which 95% of HTTP requests completed |
| Latency P99 | Duration below which 99% of HTTP requests completed |
| Requests by Route and Status | Request rate grouped by method, route, and response status |
| Latency Percentiles | P50, P95, and P99 HTTP duration over time |
| Controlled Scenarios | Rate of intentional latency and error scenarios by outcome |
| Scenario and Dependency P95 | P95 duration of controlled scenarios and simulated dependencies |
| Application Logs | Recent structured logs with trace correlation |

The `Route` variable filters the HTTP request and latency panels. Select `All` for a
service-wide view or select individual routes for focused analysis.

## Interpret the indicators

The dashboard uses thresholds as investigation cues rather than production SLOs:

- error rate below 1% is green, from 1% to below 5% is yellow, and 5% or higher is red;
- P95 below 500 ms is green, from 500 ms to below 1 second is yellow, and 1 second or
  higher is red;
- P99 below 1 second is green, from 1 second to below 2 seconds is yellow, and 2 seconds
  or higher is red.

Controlled error, latency, failure, and timeout scenarios can intentionally cross these
thresholds. A red panel during a controlled exercise confirms that the dashboard detects
the injected condition; it does not by itself indicate an unexpected platform failure.

## Investigate an error

1. Set the time range to include the event.
2. Identify the affected route and HTTP status in `Requests by Route and Status`.
3. Review the corresponding change in `Error Rate`, `Latency P95`, and `Latency P99`.
4. Locate a related entry in `Application Logs`.
5. Expand the log entry and select its `TraceID` link.
6. Inspect the trace and its span hierarchy in Tempo.
7. Use `Logs for this trace` to return to the related Loki entries.

This workflow uses the shared OpenTelemetry trace ID to move from a service-level symptom
to request-level evidence.

## No-data behavior

Rate and histogram queries require multiple Prometheus samples within the selected rate
interval. With only isolated requests, rate panels can show zero and percentile panels can
show no data. Generate sustained traffic and select a time range that contains it before
diagnosing the dashboard itself.

The repository's versioned k6 workloads will provide reproducible traffic for dashboard
demonstrations and failure investigations.

## Evidence

The reviewed dashboard evidence is stored at:

```text
docs/screenshots/grafana/application-overview-under-load.png
```

