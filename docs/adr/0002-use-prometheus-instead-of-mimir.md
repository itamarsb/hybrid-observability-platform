# ADR 0002: Use a Local Grafana Observability Stack

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

The initial release is a single-node development environment intended for repeatable demonstrations and short investigations. It does not require horizontal scaling, multi-tenancy, or long-term storage.

## Decision

Use Prometheus for metrics, Loki for logs, Tempo for traces, and Grafana for visualization and correlation. Run the stack locally with Docker Compose and pinned image versions.

Prometheus is preferred over Mimir for the initial metrics backend because the expected workload fits a single instance and does not justify Mimir's additional services and operational cost.

## Consequences

**Benefits**

- widely used query languages and operational workflows;
- low setup cost for a single-node lab;
- clear separation between collection, storage, and visualization;
- a practical path to exemplars and cross-signal navigation.

**Trade-offs**

- no high availability or horizontal scalability;
- local volumes are disposable and not a backup;
- capacity is limited by the host running Docker.

## Validation

- every service passes a health or readiness check;
- Grafana data sources are provisioned from version-controlled files;
- a test request can be followed from a metric or exemplar to a trace and related logs;
- restart tests confirm the documented persistence behavior.

## Revisit when

Consider Mimir or another scalable backend only if measured requirements include multi-tenancy, high availability, long retention, or ingestion beyond a single Prometheus instance.
