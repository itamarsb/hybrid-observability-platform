# ADR 0004: Make AWS Export Optional

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

CloudWatch and X-Ray integration demonstrates a useful hybrid scenario, but permanent export would add cost, credentials, provider dependency, and duplicated storage to the normal development workflow.

## Decision

Local mode is the default and requires no AWS credentials. Hybrid mode is enabled explicitly and adds selected CloudWatch and X-Ray exporters while the local pipeline remains active.

Enabling hybrid mode must not require application source changes. Terraform owns AWS resources, retention, tags, and teardown. Export is bounded by sampling, filtering, cardinality controls, and short test windows.

The presence of AWS credentials must never enable export automatically.

## Consequences

**Benefits**

- routine development remains free of cloud dependencies and ingestion charges;
- the same instrumentation supports local and AWS destinations;
- AWS integration remains real, reproducible, and removable.

**Trade-offs**

- two operating modes require separate validation;
- telemetry may be duplicated during hybrid runs;
- AWS quotas, permissions, and exporter behavior add failure modes.

## Validation

- local mode makes no AWS API calls;
- hybrid mode exports only approved signals and attributes;
- AWS failure does not interrupt local collection;
- Terraform destroy and a post-destroy inventory confirm cleanup;
- cost and ingestion volume are reviewed after each demonstration window.

## Alternatives considered

- **CloudWatch as the primary backend:** rejected because it conflicts with local-first operation.
- **Always-on dual export:** rejected because of cost and unnecessary duplication.
- **No AWS integration:** rejected because hybrid observability is part of the project scope.
