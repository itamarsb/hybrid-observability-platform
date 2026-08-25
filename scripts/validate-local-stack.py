#!/usr/bin/env python3
"""Validate the local Hybrid Observability Platform end to end."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SERVICES = {
    "app",
    "otel-collector",
    "prometheus",
    "loki",
    "tempo",
    "grafana",
}


class ValidationError(RuntimeError):
    """Raised when a validation check cannot be completed successfully."""


@dataclass(frozen=True)
class HttpResponse:
    """Minimal HTTP response returned by the standard-library client."""

    status: int
    body: str

    def json(self) -> Any:
        """Decode the response body as JSON."""

        try:
            return json.loads(self.body)
        except json.JSONDecodeError as error:
            raise ValidationError("response did not contain valid JSON") from error


def run_command(*arguments: str, timeout: float = 120.0) -> subprocess.CompletedProcess[str]:
    """Run a command from the repository root and capture its output."""

    try:
        return subprocess.run(
            arguments,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise ValidationError(f"command timed out after {timeout:.0f}s") from error
    except OSError as error:
        raise ValidationError(str(error)) from error


def require_success(result: subprocess.CompletedProcess[str]) -> str:
    """Return stdout or raise a concise error for a failed command."""

    if result.returncode == 0:
        return result.stdout.strip()

    detail = result.stderr.strip() or result.stdout.strip() or "command failed"
    raise ValidationError(detail.splitlines()[-1])


def http_request(
    url: str,
    *,
    accepted_statuses: set[int] | None = None,
    timeout: float = 5.0,
) -> HttpResponse:
    """Perform an HTTP GET and accept only the requested status codes."""

    accepted = accepted_statuses or {200}
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "local-stack-validator/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        status = error.code
        body = error.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as error:
        raise ValidationError(str(error.reason if hasattr(error, "reason") else error)) from error

    if status not in accepted:
        raise ValidationError(f"HTTP {status} returned by {url}")

    return HttpResponse(status=status, body=body)


def wait_until(
    probe: Callable[[], None],
    *,
    timeout: float,
    interval: float = 2.0,
) -> None:
    """Retry a probe until it succeeds or the deadline expires."""

    deadline = time.monotonic() + timeout
    last_error = "condition was not satisfied"

    while time.monotonic() < deadline:
        try:
            probe()
            return
        except ValidationError as error:
            last_error = str(error)
            time.sleep(interval)

    raise ValidationError(f"timed out after {timeout:.0f}s: {last_error}")


def check_compose_configuration() -> None:
    """Validate the resolved Compose model."""

    require_success(run_command("docker", "compose", "config", "--quiet"))


def start_stack() -> None:
    """Build and start the local stack without deleting existing data."""

    require_success(
        run_command(
            "docker",
            "compose",
            "up",
            "--detach",
            "--build",
            "--wait",
            "--wait-timeout",
            "180",
            timeout=300.0,
        )
    )


def parse_compose_processes(output: str) -> list[dict[str, Any]]:
    """Handle both JSON-array and newline-delimited Compose output."""

    if not output.strip():
        return []

    try:
        decoded = json.loads(output)
    except json.JSONDecodeError:
        try:
            return [json.loads(line) for line in output.splitlines() if line.strip()]
        except json.JSONDecodeError as error:
            raise ValidationError("Docker Compose returned invalid JSON") from error

    return decoded if isinstance(decoded, list) else [decoded]


def check_container_health() -> None:
    """Confirm that every expected Compose service is running and healthy."""

    output = require_success(run_command("docker", "compose", "ps", "--format", "json"))
    processes = parse_compose_processes(output)
    by_service = {str(process.get("Service")): process for process in processes}
    missing = EXPECTED_SERVICES - by_service.keys()
    if missing:
        raise ValidationError(f"missing services: {', '.join(sorted(missing))}")

    failures: list[str] = []
    for service in sorted(EXPECTED_SERVICES):
        process = by_service[service]
        state = str(process.get("State", "")).lower()
        health = str(process.get("Health", "")).lower()
        if state != "running" or health not in {"", "healthy"}:
            failures.append(f"{service} state={state or 'unknown'} health={health or 'unknown'}")

    if failures:
        raise ValidationError("; ".join(failures))


def check_json_endpoint(url: str, expected: dict[str, Any] | None = None) -> None:
    """Require a successful JSON endpoint and optionally match top-level fields."""

    payload = http_request(url).json()
    if not isinstance(payload, dict):
        raise ValidationError(f"unexpected response from {url}")
    for key, value in (expected or {}).items():
        if payload.get(key) != value:
            raise ValidationError(f"expected {key}={value!r}, received {payload.get(key)!r}")


def check_prometheus_targets() -> None:
    """Confirm that all configured Prometheus scrape targets are healthy."""

    payload = http_request("http://127.0.0.1:9090/api/v1/targets?state=active").json()
    targets = payload.get("data", {}).get("activeTargets", [])
    expected_jobs = {"prometheus", "otel-collector-internal", "application-metrics"}
    healthy_jobs = {
        target.get("labels", {}).get("job")
        for target in targets
        if target.get("health") == "up"
    }
    missing = expected_jobs - healthy_jobs
    if missing:
        raise ValidationError(f"Prometheus targets not up: {', '.join(sorted(missing))}")


def generate_validation_traffic() -> None:
    """Generate deterministic metrics, logs, and traces for backend queries."""

    http_request("http://127.0.0.1:8000/api/v1/items/1")
    http_request("http://127.0.0.1:8000/api/v1/scenarios/latency?delay_ms=100")
    http_request(
        "http://127.0.0.1:8000/api/v1/scenarios/error",
        accepted_statuses={500, 503},
    )


def prometheus_query(expression: str) -> list[dict[str, Any]]:
    """Execute an instant Prometheus query and return its result vector."""

    query = urllib.parse.urlencode({"query": expression})
    payload = http_request(f"http://127.0.0.1:9090/api/v1/query?{query}").json()
    if payload.get("status") != "success":
        raise ValidationError("Prometheus query failed")
    return payload.get("data", {}).get("result", [])


def check_application_metrics() -> None:
    """Confirm that custom scenario metrics reached Prometheus."""

    result = prometheus_query('{__name__=~"app_scenario_requests.*"}')
    if not result:
        raise ValidationError("custom application metrics were not found")


def loki_query() -> list[dict[str, Any]]:
    """Query recent application logs stored by Loki."""

    now_ns = time.time_ns()
    parameters = urllib.parse.urlencode(
        {
            "query": '{service_name="hybrid-observability-api"}',
            "start": str(now_ns - 300_000_000_000),
            "end": str(now_ns),
            "limit": "20",
            "direction": "backward",
        }
    )
    payload = http_request(f"http://127.0.0.1:3100/loki/api/v1/query_range?{parameters}").json()
    if payload.get("status") != "success":
        raise ValidationError("Loki query failed")
    return payload.get("data", {}).get("result", [])


def check_application_logs() -> None:
    """Confirm that recent application logs reached Loki."""

    if not loki_query():
        raise ValidationError("application logs were not found")


def tempo_search() -> list[dict[str, Any]]:
    """Search Tempo for recently generated application traces."""

    parameters = urllib.parse.urlencode(
        {
            "tags": "service.name=hybrid-observability-api",
            "start": str(int(time.time()) - 300),
            "end": str(int(time.time())),
            "limit": "20",
        }
    )
    payload = http_request(f"http://127.0.0.1:3200/api/search?{parameters}").json()
    return payload.get("traces", [])


def check_application_traces() -> None:
    """Confirm that recent application traces reached Tempo."""

    if not tempo_search():
        raise ValidationError("application traces were not found")


def build_checks(timeout: float) -> list[tuple[str, Callable[[], None]]]:
    """Build the ordered validation contract."""

    return [
        ("Docker Compose configuration", check_compose_configuration),
        ("Stack startup", start_stack),
        ("Container health", check_container_health),
        (
            "OpenTelemetry Collector health",
            lambda: check_json_endpoint("http://127.0.0.1:13133/"),
        ),
        ("Prometheus health", lambda: http_request("http://127.0.0.1:9090/-/healthy")),
        ("Loki health", lambda: http_request("http://127.0.0.1:3100/ready")),
        ("Tempo health", lambda: http_request("http://127.0.0.1:3200/ready")),
        (
            "Grafana health",
            lambda: check_json_endpoint(
                "http://127.0.0.1:3000/api/health", {"database": "ok"}
            ),
        ),
        (
            "Application liveness endpoint",
            lambda: check_json_endpoint("http://127.0.0.1:8000/health/live"),
        ),
        (
            "Application readiness endpoint",
            lambda: check_json_endpoint("http://127.0.0.1:8000/health/ready"),
        ),
        ("Prometheus targets", check_prometheus_targets),
        ("Validation traffic", generate_validation_traffic),
        (
            "Application metrics received by Prometheus",
            lambda: wait_until(check_application_metrics, timeout=timeout),
        ),
        (
            "Application logs received by Loki",
            lambda: wait_until(check_application_logs, timeout=timeout),
        ),
        (
            "Application traces received by Tempo",
            lambda: wait_until(check_application_traces, timeout=timeout),
        ),
    ]


def parse_arguments() -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--telemetry-timeout",
        type=float,
        default=60.0,
        help="seconds to wait for metrics, logs, and traces (default: 60)",
    )
    return parser.parse_args()


def main() -> int:
    """Run every check and return a process-friendly exit code."""

    arguments = parse_arguments()
    print("Hybrid Observability Platform - Local Validation\n")

    if shutil.which("docker") is None:
        print("[FAIL] Docker CLI: executable not found in PATH")
        return 1

    checks = build_checks(arguments.telemetry_timeout)
    passed = 0

    for name, check in checks:
        try:
            check()
        except ValidationError as error:
            print(f"[FAIL] {name}: {error}")
            print(f"\nValidation failed: {passed}/{len(checks)} checks passed.")
            return 1
        except Exception as error:  # Defensive boundary for actionable CLI output.
            print(f"[FAIL] {name}: unexpected error: {error}")
            print(f"\nValidation failed: {passed}/{len(checks)} checks passed.")
            return 1
        else:
            passed += 1
            print(f"[PASS] {name}")

    print(f"\nValidation completed successfully: {passed}/{len(checks)} checks passed.")
    print("The stack remains running and all named volumes are preserved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

