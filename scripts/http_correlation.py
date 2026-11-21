"""Parse and validate request-specific Loki and Tempo evidence.

These pure helpers have no network or Docker dependency, enabling isolated unit tests.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
from typing import Any


TRACE_ID_PATTERN = re.compile(r"[0-9a-f]{32}\Z")
ERROR_ROUTE = "/api/v1/scenarios/error"
ERROR_EVENT = "controlled_scenario_failed"


def trace_id_from_response(payload: Any) -> str:
    """Require the 32-digit, nonzero trace ID returned by the HTTP 503 API."""

    if not isinstance(payload, dict):
        raise ValueError("controlled-error response is not a JSON object")
    if payload.get("error") != "controlled_service_failure":
        raise ValueError("unexpected controlled-error response code")

    trace_id = payload.get("trace_id")
    if not isinstance(trace_id, str) or not TRACE_ID_PATTERN.fullmatch(trace_id):
        raise ValueError("controlled-error response contains no valid trace ID")
    if trace_id == "0" * 32:
        raise ValueError("controlled-error trace ID must not be zero")
    return trace_id


def _decode_log_line(line: Any) -> dict[str, Any] | None:
    """Decode a structured log line, optionally wrapped by a logging driver."""

    if not isinstance(line, str):
        return None
    try:
        record = json.loads(line)
        if isinstance(record, dict) and isinstance(record.get("log"), str):
            record = json.loads(record["log"].strip())
    except (TypeError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def loki_has_correlated_error(payload: Any, trace_id: str) -> bool:
    """Match an exact ID, event, route and HTTP status in Loki log entries."""

    if not isinstance(payload, dict) or payload.get("status") != "success":
        return False
    data = payload.get("data")
    if not isinstance(data, dict):
        return False

    for stream in data.get("result", []):
        if not isinstance(stream, dict):
            continue
        for entry in stream.get("values", []):
            if not isinstance(entry, list) or len(entry) < 2:
                continue
            log = _decode_log_line(entry[1])
            if log is None:
                continue
            if (
                log.get("trace_id") == trace_id
                and log.get("message") == ERROR_EVENT
                and log.get("path") == ERROR_ROUTE
                and log.get("status_code") == 503
            ):
                return True
    return False


def _attribute_value(attributes: Any, name: str) -> str | None:
    """Read an OpenTelemetry JSON attribute as a comparable string."""

    if not isinstance(attributes, list):
        return None
    for attribute in attributes:
        if not isinstance(attribute, dict) or attribute.get("key") != name:
            continue
        value = attribute.get("value")
        if isinstance(value, dict):
            for key in ("stringValue", "intValue"):
                if key in value:
                    return str(value[key])
    return None


def _span_trace_id(value: Any) -> str | None:
    """Normalize OTLP/JSON base64 trace IDs (and hex IDs) to lowercase hex."""

    if not isinstance(value, str):
        return None
    if TRACE_ID_PATTERN.fullmatch(value):
        return value
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        return None
    return raw.hex() if len(raw) == 16 else None


def tempo_has_correlated_error(payload: Any, trace_id: str) -> bool:
    """Require a matching server span for the controlled route and HTTP 503."""

    if not isinstance(payload, dict):
        return False
    trace = payload.get("trace", payload)
    if not isinstance(trace, dict):
        return False
    resource_spans = trace.get("resourceSpans", [])
    if not isinstance(resource_spans, list):
        return False

    for resource in resource_spans:
        if not isinstance(resource, dict):
            continue
        resource_attributes = resource.get("resource", {}).get("attributes", [])
        if _attribute_value(resource_attributes, "service.name") != "hybrid-observability-api":
            continue
        for scope in resource.get("scopeSpans", []):
            if not isinstance(scope, dict):
                continue
            for span in scope.get("spans", []):
                if not isinstance(span, dict):
                    continue
                attributes = span.get("attributes", [])
                route = _attribute_value(attributes, "http.route")
                status = (
                    _attribute_value(attributes, "http.response.status_code")
                    or _attribute_value(attributes, "http.status_code")
                )
                if (
                    _span_trace_id(span.get("traceId")) == trace_id
                    and span.get("kind") in ("SPAN_KIND_SERVER", 2, "2")
                    and route == ERROR_ROUTE
                    and status == "503"
                ):
                    return True
    return False
