# ADR 0005: Apply Bounded Telemetry Retention

- **Status:** Accepted
- **Date:** 2026-08-21
- **Decision owners:** Project maintainer
- **Scope:** Local and hybrid telemetry storage
- **Related decisions:** ADR 0001, ADR 0002, ADR 0003, ADR 0004

---

## Context

The Hybrid Observability Platform generates and stores:

- application metrics;
- infrastructure metrics;
- application logs;
- container logs;
- OpenTelemetry Collector internal telemetry;
- distributed traces;
- synthetic workload telemetry;
- optional AWS telemetry.

Observability data grows continuously while ingestion remains active.

Even a small development environment can consume significant storage when it uses:

- frequent metric collection;
- high-cardinality labels;
- verbose application logs;
- unsampled traces;
- repeated health checks;
- long-running load tests;
- persistent Docker volumes;
- cloud log groups without expiration.

Unbounded retention creates risks including:

- workstation disk exhaustion;
- Docker virtual-disk growth;
- application instability;
- observability backend failure;
- excessive memory consumption;
- unnecessary AWS charges;
- retention of sensitive operational data;
- slower queries;
- difficult cleanup;
- misleading long-term datasets.

The project does not require permanent telemetry history.

Its telemetry exists primarily to support:

- pipeline validation;
- operational dashboards;
- controlled workload analysis;
- metrics, logs, and traces correlation;
- failure and recovery scenarios;
- portfolio evidence;
- AWS integration validation.

Retention must therefore be explicit, bounded, measurable, and testable.

---

## Decision

All telemetry backends must apply bounded retention.

The initial retention baseline is:

| Backend | Signal or state | Initial retention |
|---|---|---:|
| Prometheus | Metrics | 48 hours |
| Loki | Logs | 24 hours |
| Tempo | Traces | 24 hours |
| Grafana | Dashboards and runtime state | Project lifecycle |
| CloudWatch Logs | Hybrid logs | 1 day |
| AWS X-Ray | Hybrid traces | AWS-managed 30 days |
| CloudWatch metrics | Hybrid metrics | AWS-managed service retention |
| k6 result files | Load-test evidence | Removed after review unless intentionally preserved |

Local telemetry is intentionally disposable.

The project will retain source code, configuration, dashboards, rules, tests, and documentation in Git. It will not retain runtime telemetry in Git.

Time-based retention will be combined with ingestion controls and, where supported, size-based limits.

Retention configuration is considered a required operational control, not an optional optimization.

---

## Decision Drivers

### Local disk protection

The platform must not consume unrestricted space on the development workstation or Docker virtual disk.

### Cloud cost control

Cloud logs, custom metrics, and traces must not be retained or generated without deliberate limits.

### Data minimization

Operational telemetry should not be stored longer than required for its defined purpose.

### Reproducibility

Important scenarios can be regenerated through version-controlled applications and controlled workloads.

### Query performance

Short retention reduces the amount of data scanned and maintained in the development environment.

### Explicit lifecycle

The project must define when telemetry expires and how full cleanup is performed.

### Security and privacy

Short retention reduces the exposure window for operational metadata and accidentally collected sensitive attributes.

---

## Retention Is Not Backup

Retention defines how long a backend keeps telemetry available for normal querying.

Retention does not provide:

- backup;
- disaster recovery;
- archival guarantees;
- legal preservation;
- immutable evidence;
- protection against volume deletion;
- protection against storage corruption.

The project does not require backup of routine runtime telemetry.

Reproducibility is provided through:

- source code;
- version-controlled configuration;
- dashboards;
- alerting and recording rules;
- k6 workload profiles;
- deployment automation;
- validation procedures.

Telemetry that must be preserved for a report or portfolio artifact must follow a separate reviewed evidence process.

---

## Prometheus Retention

Prometheus will initially retain metrics for:

```text
48 hours
```

Prometheus retention must be configured explicitly.

The implementation must not depend on the default retention period.

Where supported by the selected Prometheus version, the project should combine:

- time-based retention;
- size-based retention or a storage-capacity guardrail.

The effective retention may be shorter when a configured size limit is reached.

Prometheus storage planning must account for:

- active time-series count;
- scrape interval;
- samples per series;
- histograms;
- exemplars;
- recording rules;
- write-ahead log;
- block compaction;
- label cardinality.

The project must measure actual disk consumption before increasing retention.

---

## Loki Retention

Loki will initially retain logs for:

```text
24 hours
```

Retention must be explicitly enabled through the Loki retention mechanism supported by the pinned version and selected storage mode.

The implementation must validate:

- retention is enabled;
- the selected index schema supports retention;
- the Compactor or equivalent retention component is active;
- the delete-request store is configured when required;
- expired index references are removed;
- expired chunks are eventually deleted;
- deletion delay is understood;
- storage permissions allow deletion.

Loki deletion may be asynchronous.

Data passing the retention threshold is not necessarily removed from disk immediately.

The project must distinguish between:

- data no longer returned by queries;
- data marked for deletion;
- data physically removed from storage.

Logs must also be controlled before storage through:

- appropriate severity levels;
- health-check filtering;
- duplicate-event reduction;
- bounded attributes;
- sensitive-field removal;
- controlled workload duration.

---

## Tempo Retention

Tempo will initially retain traces for:

```text
24 hours
```

The retention mechanism must be compatible with:

- the pinned Tempo version;
- monolithic local deployment;
- local filesystem storage;
- the selected compaction architecture.

Tempo retention behavior may change between major versions. The implementation must not copy an outdated compactor configuration without validating it against the pinned image version.

Trace storage must also be controlled through:

- trace sampling;
- reduced sampling of repetitive health checks;
- bounded span attributes;
- limited workload duration;
- controlled span generation;
- exclusion of unnecessary payloads.

Retention alone is not sufficient to protect trace storage when ingestion is unbounded.

---

## Grafana State

Grafana dashboards and provisioned data sources are configuration artifacts and should be version-controlled where possible.

Grafana runtime state may persist for the project lifecycle to preserve:

- local preferences;
- user configuration;
- runtime metadata;
- provisioned dashboard state.

Grafana runtime data must remain separate from telemetry storage.

Removing the Grafana runtime volume must not remove version-controlled dashboards or provisioning definitions.

No production credentials or irreplaceable dashboard configuration should exist only inside the Grafana runtime database.

---

## CloudWatch Logs Retention

Project-created CloudWatch log groups will initially use:

```text
1 day
```

Retention must be defined through Terraform whenever the log group is managed by the project.

The implementation must not rely on indefinite CloudWatch Logs retention.

The project must verify:

- the log group exists in the intended account and region;
- the expected retention policy is active;
- only approved log streams are receiving events;
- log ingestion stops when hybrid mode is disabled;
- log groups are removed when their lifecycle requires removal.

A one-day policy does not prevent ingestion charges. It limits storage duration after ingestion.

---

## AWS X-Ray Retention

AWS X-Ray trace data is retained by AWS for:

```text
30 days
```

This retention period is AWS-managed and is not configurable by the project.

The platform will control X-Ray data volume through:

- optional hybrid mode;
- bounded validation windows;
- trace sampling;
- controlled workload generation;
- attribute filtering;
- explicit exporter activation.

Because X-Ray retention cannot be reduced below the service-defined period, the project must minimize data before export.

Local Tempo remains the primary trace backend.

---

## CloudWatch Metrics Retention

CloudWatch metric retention is managed by AWS and includes automatic resolution rollups over time.

The project cannot use a short retention setting to immediately remove published custom metrics.

CloudWatch metric volume must therefore be controlled before publication through:

- metric allowlists;
- bounded labels or dimensions;
- standard resolution where sufficient;
- controlled publication intervals;
- avoidance of duplicate host metrics;
- short hybrid execution windows;
- disabled-by-default cloud export.

Published metrics may remain visible after the associated compute resources or exporters are removed.

This behavior must not be interpreted as failed Terraform cleanup.

---

## Load-Test Result Retention

k6 output can include:

- summaries;
- raw event data;
- time-series results;
- generated reports;
- failure details.

Raw load-test results must not be retained indefinitely.

After each test, results must be classified as:

- temporary runtime data;
- reviewed engineering evidence;
- discarded output.

Only reviewed and sanitized evidence may be committed.

Raw high-volume k6 output must remain ignored by Git.

---

## Multi-Layer Retention Controls

Retention must be implemented at several layers.

### Source controls

- bounded workload duration;
- bounded request rate;
- bounded virtual users;
- appropriate log levels;
- trace sampling;
- normalized application routes.

### Collector controls

- memory limiter;
- batch processor;
- filters;
- attribute removal;
- bounded queues;
- bounded retries;
- sampling where applicable.

### Backend controls

- time-based retention;
- size-based retention where supported;
- compaction;
- deletion;
- project-specific volumes;
- explicit storage paths.

### Cloud controls

- short log-group retention;
- restricted metric publication;
- controlled trace sampling;
- explicit hybrid-mode activation;
- resource cleanup.

No single layer is sufficient by itself.

---

## Size-Based Guardrails

Time-based retention does not prevent rapid disk exhaustion during unusually high ingestion.

Where supported, local backends should also use:

- maximum storage size;
- maximum disk-usage percentage;
- ingestion limits;
- query limits;
- rate limits.

Exact size values will be established after measuring the first validated deployment.

They must reflect:

- workstation free space;
- Docker virtual-disk allocation;
- expected ingestion rate;
- compaction overhead;
- temporary write amplification;
- safety margin.

At least one operational procedure must define how to detect storage approaching its limit.

---

## Retention Validation

Retention is not considered active merely because a configuration value exists.

Validation must demonstrate that:

1. telemetry is ingested;
2. telemetry remains queryable within the retention window;
3. data outside the window stops appearing in queries;
4. backend deletion processes are healthy;
5. physical storage consumption eventually decreases or stabilizes;
6. recent data remains available;
7. no unrelated project data is removed.

Retention tests must use timestamps and controlled datasets that make expiration observable.

---

## Monitoring Retention Health

The platform should expose or collect evidence for:

- backend disk consumption;
- ingestion rate;
- active series;
- stored log volume;
- trace volume;
- compaction status;
- retention failures;
- deletion failures;
- available disk space;
- Docker volume growth.

A backend reporting healthy ingestion while retention is failing must not be considered fully healthy.

---

## Cleanup

Retention handles normal data expiration.

Full cleanup handles project decommissioning.

The project must provide a reviewed procedure that removes:

- project containers;
- project networks;
- project telemetry volumes;
- temporary load-test data;
- generated runtime configuration;
- managed AWS resources when applicable.

Cleanup must not remove:

- unrelated Docker volumes;
- other repositories;
- personal files;
- TCC2 data;
- unrelated AWS resources;
- shared credentials.

Broad commands that delete all Docker volumes, containers, images, or AWS resources are prohibited from normal project documentation.

---

## Security Considerations

Telemetry retention affects security because metrics, logs, and traces may contain operational metadata.

Short retention reduces but does not eliminate the risk of:

- credential exposure;
- personal-data exposure;
- internal topology disclosure;
- endpoint discovery;
- infrastructure metadata leakage;
- exception-detail exposure.

Sensitive telemetry must be filtered before storage.

Retention must not be used as a substitute for:

- secret removal;
- access control;
- network isolation;
- encryption;
- safe logging;
- telemetry redaction.

If a secret is collected, waiting for retention to expire is not an acceptable response. The secret must be revoked and rotated.

---

## Privacy Considerations

The project will use synthetic and project-owned data.

No retention setting authorizes collection of:

- production customer data;
- private communications;
- third-party telemetry;
- personal browsing information;
- real payment data;
- unnecessary personal identifiers.

Data minimization applies before ingestion, not only after the retention period.

---

## Cost Considerations

Local retention primarily affects:

- workstation SSD consumption;
- Docker disk growth;
- memory consumption;
- CPU used by compaction and queries.

AWS retention primarily affects:

- log storage;
- metrics retained under AWS service behavior;
- trace ingestion and managed retention;
- query and analysis operations.

Short retention reduces some storage costs but does not eliminate:

- ingestion charges;
- custom metric charges;
- trace recording charges;
- query charges;
- resource costs.

Cost validation must therefore evaluate both ingestion and retention.

---

## Alternatives Considered

### Use backend default retention values

This option was rejected because defaults:

- differ between products and versions;
- may be significantly longer than required;
- may retain data indefinitely;
- may change during upgrades;
- do not represent an explicit engineering decision.

### Delete all data manually after every run

This option was rejected because it would:

- prevent historical dashboard validation;
- prevent restart and recovery testing;
- rely on manual discipline;
- provide no protection during forgotten or long-running sessions.

Manual cleanup remains a decommissioning mechanism, not the normal retention strategy.

### Retain all local telemetry indefinitely

This option was rejected because it would:

- consume workstation storage;
- increase operational risk;
- provide little additional project value;
- complicate privacy and cleanup;
- make backend behavior harder to control.

### Use only size-based retention

This option was rejected because it would not provide a predictable time window for dashboards and validation.

Size-based limits complement but do not replace time-based retention.

### Use only time-based retention

This option was rejected as the complete strategy because sudden high-volume ingestion can exhaust storage before time-based expiration occurs.

### Use cloud storage for long-term retention

This option was rejected for the initial implementation because:

- the project does not require long-term history;
- cloud storage would increase cost and complexity;
- telemetry scenarios can be reproduced;
- the default architecture is local-first.

### Preserve telemetry on the TCC2 laboratory computer

This option was rejected because the dedicated laboratory computer must remain separated from this portfolio environment.

---

## Consequences

### Positive consequences

- Predictable telemetry lifecycle.
- Reduced workstation storage risk.
- Lower cloud storage expenditure.
- Reduced sensitive-data exposure window.
- Faster local queries over bounded datasets.
- Easier environment cleanup.
- Explicit operational responsibility.
- Reproducible rather than permanent telemetry evidence.

### Negative consequences

- Historical telemetry expires quickly.
- Long-term trend analysis is unavailable.
- Missed validation windows may require workload regeneration.
- Retention mechanisms add configuration complexity.
- Deletion may be asynchronous.
- Physical disk usage may not decrease immediately.
- AWS-managed retention cannot always be shortened.

### Operational risks

- Retention may appear configured but remain inactive.
- Loki deletion may fail because of Compactor or storage configuration.
- Tempo configuration may become incompatible after a major upgrade.
- Prometheus write-ahead logs may temporarily exceed expected size.
- Docker virtual-disk files may not shrink immediately after internal deletion.
- CloudWatch ingestion may continue after local containers are stopped.
- X-Ray traces remain for the AWS-managed retention period.
- Size limits that are too low may remove useful telemetry prematurely.

---

## Migration Conditions

Retention periods may be increased if the project introduces:

- longer performance baselines;
- SLI and SLO evaluation windows;
- multi-day incident scenarios;
- trend analysis;
- capacity planning;
- academic experiments requiring longer observation;
- dedicated storage infrastructure.

Retention periods may be reduced if measurements show:

- excessive disk consumption;
- unnecessary telemetry volume;
- unsafe cloud cost;
- data-minimization concerns;
- limited analytical value.

Material changes require documentation and may require a new ADR if they alter the storage strategy.

---

## Validation Criteria

This decision will be considered successfully implemented when:

- Prometheus retention is explicitly configured;
- Loki retention is explicitly enabled and validated;
- Tempo retention is explicitly configured and validated;
- CloudWatch log groups use one-day retention;
- X-Ray managed retention is documented;
- CloudWatch metric retention behavior is documented;
- k6 raw outputs are excluded from Git;
- disk consumption can be measured per project backend;
- telemetry expires according to the expected lifecycle;
- deletion and compaction failures are observable;
- local data survives ordinary restarts within the retention window;
- full project cleanup removes only project-owned telemetry;
- AWS export remains time- and volume-bounded.

---

## Reversibility

This decision is reversible.

Individual retention periods may be changed through reviewed configuration.

Changing from bounded development retention to long-term or permanent telemetry storage requires a new architectural assessment covering:

- storage capacity;
- backup;
- recovery;
- cost;
- privacy;
- security;
- query performance;
- availability;
- operational ownership.

---

## References

- [Prometheus storage and retention](https://prometheus.io/docs/prometheus/latest/storage/)
- [Prometheus configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Grafana Loki retention](https://grafana.com/docs/loki/latest/operations/storage/retention/)
- [Grafana Loki log deletion](https://grafana.com/docs/loki/latest/operations/storage/logs-deletion/)
- [Grafana Tempo configuration](https://grafana.com/docs/tempo/latest/configuration/)
- [Grafana Tempo architecture](https://grafana.com/docs/tempo/latest/introduction/architecture/)
- [AWS X-Ray concepts and retention](https://docs.aws.amazon.com/xray/latest/devguide/xray-concepts.html)
- [AWS X-Ray service quotas](https://docs.aws.amazon.com/general/latest/gr/xray.html)
- [CloudWatch Logs retention and cost optimization](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt-observability.html)
- [Amazon CloudWatch metric concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html)
