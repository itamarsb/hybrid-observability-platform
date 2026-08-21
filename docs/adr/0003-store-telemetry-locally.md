# ADR 0003: Keep Local Telemetry Ephemeral

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

The platform produces continuously growing runtime data. The project needs enough history for demonstrations and troubleshooting, but not archival storage. Unbounded data can exhaust local disk space and amplify cloud costs.

## Decision

Store routine telemetry in project-owned Docker volumes with explicit retention:

| Backend | Initial target |
|---|---:|
| Prometheus | 48 hours |
| Loki | 24 hours |
| Tempo | 24 hours |
| CloudWatch Logs, when enabled | 1 day |

Runtime telemetry, backend databases, and generated load-test results are not committed to Git. Only reviewed dashboards, configuration, test fixtures, and sanitized evidence belong in the repository.

Retention is combined with trace sampling, log-level controls, cardinality limits, bounded test duration, and storage monitoring. Cleanup commands must target only volumes owned by this Compose project.

## Consequences

**Benefits**

- predictable workstation storage use;
- lower exposure of accidentally collected data;
- reproducible scenarios replace long-lived datasets;
- cloud demonstrations remain cost-aware.

**Trade-offs**

- historical telemetry expires;
- evidence must be intentionally reviewed and exported;
- retention behavior varies by backend version and must be tested.

## Validation

- retention settings are present in effective runtime configuration;
- expired data becomes unavailable within the documented backend behavior;
- disk usage remains within the defined test budget;
- cleanup removes project data without affecting unrelated Docker volumes.
