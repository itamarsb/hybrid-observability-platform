# Security Policy

## Supported versions

The project is under active development and has no stable release. Only the latest commit on `main` is supported on a best-effort basis.

## Reporting a vulnerability

Do not disclose suspected vulnerabilities in public issues, discussions, or pull requests. Use [GitHub Private Vulnerability Reporting](https://github.com/itamarsb/hybrid-observability-platform/security/advisories/new).

Include the affected component or commit, reproduction steps, expected and observed behavior, and a concise impact assessment. Remove credentials, tokens, account identifiers, personal data, production telemetry, and Terraform state from every report.

## Project security baseline

- Never commit credentials, secrets, private keys, real `.env` files, `.tfvars`, or Terraform state.
- Prefer temporary AWS credentials and least-privilege roles.
- Keep Grafana, Prometheus, Loki, Tempo, Collector administration endpoints, and Docker interfaces private by default.
- Do not record authentication headers, tokens, passwords, request bodies, or unnecessary personal data in telemetry.
- Run containers with pinned versions, health checks, resource limits, and non-root users where supported.
- Treat dashboards, logs, traces, screenshots, and exported test results as potentially sensitive.
- Use k6 only against systems you own or are explicitly authorized to test.
- Review Terraform plans before applying them and verify that hybrid resources are removed after use.
- Rotate any credential immediately if it is exposed, then remove it from Git history where necessary.

## Scope and limitations

This repository is a reference implementation, not a managed service. It does not provide guaranteed response times, production hardening, regulatory compliance, or security certification. Dependencies and example configurations must be reviewed before reuse in another environment.
