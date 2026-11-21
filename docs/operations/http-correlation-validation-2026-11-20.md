# Local HTTP Correlation Validation — 2026-11-20

## Scope

A local integration run verified the six-service Docker Compose deployment and
the request-specific HTTP 503 correlation check added to the cross-platform
validator. The run was observed in Windows PowerShell from the repository root.

This record summarizes the observed command output. The console screenshot
supporting the record was provided for review but has not yet been added to
the repository's version-controlled screenshot directory.

## Commands

```powershell
git pull origin main
python -m unittest discover -s scripts/tests -v
python .\scripts\validate-local-stack.py --telemetry-timeout 120
```

The Git working tree was reported as up to date after the pull.

## Observed results

| Check | Observed result |
|---|---|
| Isolated correlation tests | 11 tests executed; `OK` |
| Compose configuration | PASS |
| Stack startup | PASS |
| Container health | PASS |
| Collector, Prometheus, Loki, Tempo, and Grafana health | PASS |
| Application liveness and readiness | PASS |
| Prometheus targets | PASS |
| Controlled validation traffic | PASS |
| Application metrics in Prometheus | PASS |
| Application logs in Loki | PASS |
| Application traces in Tempo | PASS |
| Same-request HTTP 503 correlation | PASS |
| Full validator result | **16/16 checks passed** |

The final correlation check reported:

```text
[PASS] HTTP 503 metrics, log, and trace correlation
Validation completed successfully: 16/16 checks passed.
The stack remains running and all named volumes are preserved.
```

The validator printed a nonzero, 32-character hexadecimal trace ID for the
controlled HTTP 503 response. Its correlation check required:

1. Route/status aggregate metrics for the controlled HTTP 503 in Prometheus.
2. A structured error event in Loki with the same trace ID as the response.
3. A Tempo HTTP server span under that exact trace ID, with the expected
   service, route, and response status.

This supports **automated same-request correlation between response, Loki,
and Tempo**. Prometheus metrics demonstrate route-level error observations,
not an individually trace-linked metric exemplar.

## Evidence boundaries

- This is a local operator-run integration result, not a GitHub Actions
  full-platform CI result.
- Unit-test success and full-stack success are distinct observations.
- The test verifies backend data using their APIs; it does not independently
  verify the Grafana dashboard navigation or screenshots of its panels.
- The existing validation screenshot in the repository may depict the older
  15-check workflow; it must not be relabeled as evidence of this 16-check run.
- Runtime logs, trace payloads, and backend volumes are not committed.

## Reproduce

On an authorized local development machine with Docker running:

```powershell
python -m unittest discover -s scripts/tests -v
python .\scripts\validate-local-stack.py --telemetry-timeout 120
```

For the investigation workflow, see
[HTTP Error Investigation Runbook](http-error-investigation.md).
For validator prerequisites and cleanup, see
[Local Stack Validation](local-stack-validation.md).
