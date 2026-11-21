# HTTP Error Investigation Runbook

## Purpose and scope

Investigate a controlled HTTP error in the local FastAPI workload by moving from
aggregate Prometheus metrics to a request-specific Loki log and its Tempo trace.
This is an operator workflow. The local validator also includes an automated
HTTP 503 correlation check, but its full-stack execution result has not yet
been recorded. Aggregate Prometheus metrics are associated with the same
route/status, not with an individual trace ID.

The primary exercise uses `GET /api/v1/scenarios/error`, which deliberately returns
HTTP 503. The dependency scenarios provide optional HTTP 502 and 504 variants.
The procedure is for local, authorized testing; it does not simulate production
incident response or require cloud resources.

## Prerequisites

- Docker Engine or Docker Desktop and Docker Compose v2 are available.
- The local stack has been started and validated using
  `python scripts/validate-local-stack.py` (or `python3`).
- Grafana is available at <http://127.0.0.1:3000>.
- Prometheus is available at <http://127.0.0.1:9090>.
- The dashboard `Application Overview` is provisioned in Grafana.
- The `Prometheus`, `Loki`, and `Tempo` data sources are healthy.

The validator intentionally sends a 503 request and leaves the containers and
named volumes running. A new request below provides a distinct trace ID for this
investigation. In local Compose mode, trace sampling is set to 100%; a different
sampling configuration may prevent an individual trace from being retained.

## 1. Generate and identify the request

From the host machine, execute the appropriate command:

Windows PowerShell:

~~~powershell
curl.exe -sS -i http://127.0.0.1:8000/api/v1/scenarios/error
~~~

Linux or macOS:

~~~bash
curl -sS -i http://127.0.0.1:8000/api/v1/scenarios/error
~~~

Expected response properties:

- HTTP status: `503 Service Unavailable`.
- JSON `error`: `controlled_service_failure`.
- A non-null, 32-character hexadecimal `trace_id` while tracing is enabled.

Record the request time (including timezone), endpoint, HTTP status, and exact
`trace_id` returned by the API. Do not reuse a trace ID from another exercise.
The trace ID is the primary request-level join key; the timestamp narrows the
search window. Do not commit raw runtime traces or logs to the repository.

## 2. Establish the metric-level symptom in Prometheus

Open the `Application Overview` dashboard and choose a time range containing
the request. Check `Requests by Route and Status`, `Error Rate`, and `Latency P95`.

In Prometheus or Grafana Explore (Prometheus data source), use:

~~~promql
sum by (http_target, http_status_code) (
  increase(
    http_server_duration_milliseconds_count{
      service_name="hybrid-observability-api",
      http_target="/api/v1/scenarios/error",
      http_status_code="503"
    }[5m]
  )
)
~~~

This query counts HTTP 503 observations over five minutes, subject to the
underlying scrape samples. Compare it with the same route without the status
filter if the relative failure rate matters:

~~~promql
sum(
  rate(
    http_server_duration_milliseconds_count{
      service_name="hybrid-observability-api",
      http_target="/api/v1/scenarios/error",
      http_status_code="503"
    }[5m]
  )
)
/
clamp_min(
  sum(
    rate(
      http_server_duration_milliseconds_count{
        service_name="hybrid-observability-api",
        http_target="/api/v1/scenarios/error"
      }[5m]
    )
  ),
  0.000001
)
~~~

The second expression is a fraction, not a percentage. Multiply by 100 to
display percentage. If the route receives only a single request, rate or
histogram panels can show no data or an uninformative result until at least
two scrapes are available. The configured scrape interval is 15 seconds.
Generate additional bounded traffic only when necessary.

**Interpretation:** Prometheus establishes a service- or route-level symptom;
it does not identify the trace of an individual HTTP request. The `trace_id`
from the HTTP response and logs performs that next step.

## 3. Find the request log in Loki

In Grafana Explore select `Loki`, set the time range to the request window,
and run:

~~~logql
{service_name="hybrid-observability-api"} |= "controlled_scenario_failed"
~~~

Find the log recorded at the request time. The application emits a structured
warning containing the event name, `path`, `status_code`, `trace_id`, and
`span_id`. Verify that `path` is `/api/v1/scenarios/error` and that
`status_code` is `503`.

To filter using the exact ID returned by the HTTP response, replace
`TRACE_ID_FROM_RESPONSE` with the 32-character hex value:

~~~logql
{service_name="hybrid-observability-api"} |= "TRACE_ID_FROM_RESPONSE"
~~~

Confirm the log's `trace_id` matches the response. The query uses a raw line
filter intentionally, so it remains useful even if log JSON is wrapped by
the container logging transport. The dashboard's original log query uses
`{service_name="hybrid-observability-api"} | json`.

## 4. Inspect the matching trace in Tempo

Expand the matching log entry and choose its `TraceID` derived-field link.
The Loki data source is provisioned to extract a 32-character `trace_id`
and open that trace in Tempo.

Alternatively, open Grafana Explore, select `Tempo`, switch to the trace-ID
query mode, and paste the value returned by the HTTP response.

Verify:

1. The trace ID is identical to the response and log values.
2. The server span represents the HTTP request to
   `/api/v1/scenarios/error` and records the error response.
3. The trace timestamps overlap the request and log window.
4. The duration and span hierarchy are consistent with the observed
   request behavior.

A controlled 503 is handled at the application layer; it is not required to
produce a separate child dependency span. For a dependency-specific
investigation, use the scenarios below.

From the Tempo trace view, use `Logs for this trace` when available to
navigate back to Loki and confirm the associated application log. The
provisioned `tracesToLogsV2` mapping uses `service.name` /
`service_name` and the trace ID to narrow results.

## 5. Optional: diagnose dependency failures

Exercise either scenario with the same metrics-to-logs-to-traces sequence:

| Request | Expected HTTP status | Expected application log |
|---|---|---|
| `/api/v1/scenarios/dependency?outcome=failure` | 502 | `dependency_failure` |
| `/api/v1/scenarios/dependency?outcome=timeout` | 504 | `dependency_timeout` |

The dependency scenarios create a `dependency.simulated` span. Inspect it
alongside the HTTP server span, compare the error type and elapsed time,
and match the resulting `trace_id` in the structured logs. These are
simulated dependencies, not external network services.

## 6. Record the investigation outcome

Record the following in a sanitized issue, test report, or reviewed evidence
set **only after observing it in the running platform**:

| Evidence | Acceptance criterion |
|---|---|
| HTTP response | Expected 503, correct error code, non-null trace ID |
| Prometheus | Route/status metric present for the investigation window |
| Loki | Application error log with matching path, status, and trace ID |
| Tempo | Trace retrievable by that exact ID with matching request details |
| Reverse navigation | Trace-to-logs returns the related event, if the link is available |

Screenshots may show the Grafana panels, the log-to-trace navigation, and the
trace view. Redact sensitive information and do not label an unexecuted
manual investigation as a passed test.

## Troubleshooting and limitations

- **No metric data:** check the Prometheus `application-metrics` target,
  wait for multiple 15-second scrapes, and include the request in the
  selected time range.
- **No error log:** confirm the Loki data source, the
  `{service_name="hybrid-observability-api"}` stream selector, the
  container logging pipeline, and the application's logging output.
- **No trace or null trace ID:** confirm `OTEL_SDK_DISABLED=false`,
  the current sampling configuration, the Collector/Tempo endpoints,
  ingestion delay, and trace retention.
- **TraceID link missing:** verify the Loki derived-field configuration in
  `observability/grafana/provisioning/datasources/datasources.yaml` and
  inspect the raw log line for a 32-character `trace_id`.
- **Trace-to-logs does not locate the event:** query Loki directly by the
  trace ID, broaden the time window, and verify the
  `service.name` → `service_name` mapping.
- **HTTP 503 has no dependency span:** this is expected for the direct
  controlled-error endpoint; use `/dependency` for nested spans.

This runbook documents a reproducible **manual** correlation procedure. The
additional automated check in `scripts/validate-local-stack.py` generates a
new HTTP 503 and validates the same trace ID in the response, Loki event,
and Tempo HTTP server span. It also checks route/status aggregate metrics in
Prometheus. The helper logic is covered by offline unit tests, but no
successful full-stack run of the new check has yet been recorded.

Run the offline tests with:

~~~bash
python -m unittest discover -s scripts/tests -v
~~~

Metric exemplars, production alerting, sustained k6 tests, and cloud export
are not prerequisites for this local exercise and should not be described
as implemented capabilities.

## References

- [Application Observability](application-observability.md)
- [Local Stack Validation](local-stack-validation.md)
- [Grafana trace-to-logs configuration](https://grafana.com/docs/grafana/latest/datasources/tempo/configure-tempo-data-source/configure-trace-to-logs/)
- [Grafana Loki LogQL queries](https://grafana.com/docs/loki/latest/query/log_queries/)
