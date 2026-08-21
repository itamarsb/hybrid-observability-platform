# ADR 0001: Use the OpenTelemetry Collector

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

The application must emit metrics, logs, and traces to local backends and, when explicitly enabled, selected AWS services. Direct integration with every destination would couple application code to storage vendors and duplicate processing rules.

## Decision

Use the OpenTelemetry Collector as the telemetry gateway. Applications send OTLP data to the Collector; the Collector applies batching, memory protection, filtering, enrichment, and sampling before exporting each signal.

Application instrumentation remains independent of Prometheus, Loki, Tempo, CloudWatch, and X-Ray. Local and hybrid exporter sets use separate, validated configuration.

## Consequences

**Benefits**

- one processing layer for all signals;
- backend changes do not require application rewrites;
- export failures can be isolated from the application;
- filtering and sampling are enforced centrally.

**Trade-offs**

- the Collector becomes another component to configure and monitor;
- invalid pipelines can drop or duplicate telemetry;
- each enabled component must be supported by the selected Collector distribution.

## Validation

- configuration validation succeeds before startup;
- the Collector exposes healthy internal telemetry;
- application requests appear in every enabled local backend;
- an unavailable exporter does not stop the local pipeline;
- secret and high-cardinality attributes are removed as designed.

## Alternatives considered

- **Direct application export:** rejected because it couples code to each backend.
- **Separate signal-specific agents:** rejected because it increases operational overhead.
- **AWS-specific collection only:** rejected because local, vendor-neutral operation is a core requirement.
