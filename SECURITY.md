# Security Policy

## Project Security Scope

The Hybrid Observability Platform is a reference implementation for local and optional AWS observability environments.

The security scope includes:

- the instrumented FastAPI reference application;
- OpenTelemetry Collector configuration;
- Prometheus, Loki, Tempo, and Grafana configuration;
- Docker images and Compose deployment definitions;
- Terraform modules and AWS environment definitions;
- GitHub Actions workflows;
- project automation scripts;
- authentication and authorization controls;
- secret and credential handling;
- telemetry exposure and retention;
- cloud cost and resource-consumption risks.

This project is not a managed service and does not provide production security certification, regulatory compliance, or guaranteed security response times.

---

## Supported Versions

The project is currently under active development and has not published a stable release.

| Version | Supported |
|---|---|
| Latest commit on `main` | Yes |
| Development branches | No |
| Unreleased local modifications | No |
| Forks and third-party distributions | No |
| Archived commits | No |

After versioned releases are introduced, this section will be updated with the corresponding support policy.

---

## Reporting a Vulnerability

Do not report suspected vulnerabilities through public GitHub Issues, Discussions, pull requests, commit messages, or social media.

Use GitHub Private Vulnerability Reporting:

[Report a vulnerability privately](https://github.com/itamarsb/hybrid-observability-platform/security/advisories/new)

A useful report should include:

- a clear description of the vulnerability;
- the affected component or configuration;
- the affected commit, branch, or release;
- reproduction steps;
- proof-of-concept material when safe to provide;
- expected and observed behavior;
- potential confidentiality, integrity, or availability impact;
- suggested mitigation, if available;
- whether the issue is already publicly known;
- any relevant logs with secrets and personal information removed.

Do not include:

- active AWS credentials;
- access tokens;
- private keys;
- session cookies;
- Terraform state files;
- unredacted account identifiers;
- personal information;
- production telemetry belonging to third parties.

Reports will be reviewed on a best-effort basis. Receipt, investigation, remediation, release, and disclosure timelines depend on severity, reproducibility, project scope, and maintainer availability.

---

## Responsible Disclosure

Reporters are requested to allow reasonable time for investigation and remediation before publicly disclosing a vulnerability.

The expected process is:

1. private report submission;
2. initial triage;
3. reproduction and impact assessment;
4. remediation planning;
5. patch development and validation;
6. coordinated disclosure when appropriate.

Security advisories may be published after a fix or mitigation is available.

Submitting a report does not authorize:

- accessing systems or data without permission;
- testing against infrastructure not owned by the reporter;
- disrupting services;
- generating uncontrolled workloads;
- attempting denial-of-service attacks;
- extracting telemetry or credentials;
- performing social engineering;
- violating applicable laws or third-party terms.

Testing must remain limited to environments owned by the reporter or environments for which the reporter has explicit authorization.

---

## Security Baseline

The project is designed around the following baseline requirements.

### Credentials and secrets

- Credentials must not be committed to the repository.
- Long-lived AWS access keys should be avoided.
- Temporary credentials and role-based access should be preferred.
- Secrets must not be embedded in Docker images.
- Secrets must not be included in Terraform variables committed to Git.
- Real `.env` and `.tfvars` files must remain local.
- Example configuration files must contain placeholders only.
- Credentials exposed in logs or traces must be treated as compromised.

### Terraform state

Terraform state can contain sensitive infrastructure data.

State files must not be:

- committed to Git;
- attached to GitHub Issues;
- included in screenshots;
- stored in public artifacts;
- shared without review.

Local state is acceptable only for isolated development environments. Any future shared environment must use an approved remote-state design with encryption, access control, locking, and versioning.

### AWS access

AWS resources must follow least-privilege principles.

The planned AWS environment will prefer:

- IAM roles instead of embedded credentials;
- AWS Systems Manager instead of direct SSH administration;
- narrowly scoped IAM policies;
- explicit resource tagging;
- bounded deployment duration;
- short log retention;
- restricted telemetry ingestion;
- resource inventory and post-destroy verification.

No AWS component should be assumed to be cost-free.

### Network exposure

Observability interfaces can reveal infrastructure, application behavior, logs, traces, and operational metadata.

The following services must not be exposed publicly by default:

- Grafana;
- Prometheus;
- Loki;
- Tempo;
- OpenTelemetry Collector administrative endpoints;
- Docker daemon interfaces;
- internal application diagnostics.

Published ports must be documented and limited to the minimum required scope.

### Grafana

The implementation must not rely on default production credentials.

Grafana configuration must account for:

- administrative credential replacement;
- restricted anonymous access;
- controlled data-source permissions;
- protected provisioning files;
- limited external exposure;
- sanitized dashboards and screenshots.

### Telemetry data

Metrics, logs, and traces may contain sensitive information.

Telemetry pipelines must avoid collecting or retaining:

- passwords;
- API keys;
- authentication headers;
- session tokens;
- private keys;
- full payment information;
- unnecessary personal information;
- request or response bodies containing confidential data.

Sensitive attributes should be removed or transformed before export whenever possible.

### Logging

Application and infrastructure logs must use appropriate severity levels.

Continuous debug logging should not be enabled by default because it can:

- expose implementation details;
- increase local storage consumption;
- increase cloud ingestion costs;
- introduce sensitive data into log backends;
- reduce signal-to-noise ratio.

### Distributed tracing

Trace instrumentation must apply controls for:

- sampling;
- sensitive attributes;
- request headers;
- query parameters;
- request and response bodies;
- retention;
- external export.

Trace propagation must not be treated as authorization.

### Containers

Container security controls should include:

- versioned image references;
- minimal base images where practical;
- non-root execution where supported;
- limited Linux capabilities;
- health checks;
- resource limits;
- read-only filesystems where applicable;
- isolated networks;
- vulnerability scanning;
- reviewed volume mounts.

Use of a container image does not imply that the image or its dependencies are trusted.

### Local storage

Local Prometheus, Loki, Tempo, and Grafana data must use project-specific storage locations or Docker volumes.

Retention and cleanup must be configured explicitly. Local telemetry data must not be assumed to disappear merely because containers are stopped.

Destructive cleanup commands must be reviewed before execution to ensure that only project-owned data is removed.

### Workload generation

k6 and other load-generation tools must be used only against explicitly authorized targets.

Load profiles must define:

- target endpoint;
- request rate;
- virtual-user limits;
- execution duration;
- timeout behavior;
- abort thresholds.

Unbounded or unauthorized load generation is outside the project scope.

---

## Cost and Resource Abuse

Observability systems can generate unexpected costs or exhaust local resources through:

- excessive metric cardinality;
- high-frequency custom metrics;
- uncontrolled log ingestion;
- unsampled traces;
- unrestricted retention;
- recursive telemetry collection;
- high-volume load tests;
- forgotten AWS resources;
- publicly accessible ingestion endpoints.

Security reports may include cost-amplification and resource-exhaustion findings when they are reproducible within the project scope.

The implementation will apply:

- bounded retention;
- controlled cardinality;
- trace sampling;
- batch processing;
- memory limiting;
- restricted endpoints;
- short AWS validation windows;
- explicit cleanup;
- post-destroy verification.

---

## Dependency Security

The project depends on third-party software and container images.

Planned controls include:

- dependency version constraints;
- container image scanning;
- Python dependency scanning;
- Terraform static analysis;
- secret scanning;
- GitHub dependency alerts;
- automated configuration validation;
- review of upstream security advisories.

A vulnerability affecting an upstream project should also be reported to the corresponding upstream maintainer when appropriate.

This repository cannot guarantee the security or availability of third-party components.

---

## Security Automation

Security automation will be added incrementally.

Planned checks include:

- secret detection;
- Python dependency analysis;
- container image scanning;
- Dockerfile linting;
- Terraform formatting and validation;
- Terraform security analysis;
- infrastructure misconfiguration detection;
- workflow permission review;
- configuration syntax validation.

Until these controls are implemented, they must not be interpreted as active protections.

---

## Handling Exposed Credentials

If a credential is committed, logged, displayed in a screenshot, or included in an artifact:

1. revoke or disable it immediately;
2. rotate the affected credential;
3. review associated access and audit logs;
4. remove the secret from the current repository state;
5. evaluate whether Git history must be rewritten;
6. invalidate derived sessions or tokens;
7. inspect cloud resources for unauthorized activity;
8. document the incident without reproducing the secret;
9. verify that secret scanning no longer detects the value.

Deleting the visible file or commit does not make an exposed credential safe to reuse.

---

## Security Limitations

The initial platform operates on a single development workstation and is intended for controlled environments.

The initial implementation will not provide:

- multi-host high availability;
- production identity federation;
- enterprise secret management;
- regulatory compliance certification;
- continuous security monitoring;
- guaranteed incident response;
- production-grade disaster recovery;
- protection for arbitrary public deployments;
- security support for modified forks.

Deployment outside the documented scope requires an independent security assessment.

---

## Safe Evidence and Screenshots

Before publishing screenshots, dashboards, logs, traces, terminal output, or cloud-console evidence, remove or obscure:

- AWS account IDs;
- email addresses;
- access keys and tokens;
- resource identifiers when unnecessary;
- public IP addresses when unnecessary;
- internal hostnames;
- user identifiers;
- billing information;
- telemetry containing personal or confidential information;
- local filesystem paths that reveal personal data.

Redaction must be performed before the evidence is committed.

---

## Contact

Security reports must be submitted through GitHub Private Vulnerability Reporting:

[https://github.com/itamarsb/hybrid-observability-platform/security/advisories/new](https://github.com/itamarsb/hybrid-observability-platform/security/advisories/new)

Public project questions that do not involve a vulnerability may use GitHub Issues after issue tracking is enabled.
