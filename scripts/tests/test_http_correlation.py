"""Offline regression tests for request-specific telemetry correlation."""

import base64
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from http_correlation import (  # noqa: E402
    loki_has_correlated_error,
    tempo_has_correlated_error,
    trace_id_from_response,
)

TRACE_ID = "a" * 32
OTHER_ID = "b" * 32


def loki_payload(*, trace_id=TRACE_ID, event="controlled_scenario_failed", path="/api/v1/scenarios/error", status=503):
    line = json.dumps({"message": event, "trace_id": trace_id, "path": path, "status_code": status})
    return {"status": "success", "data": {"result": [{"values": [["123", line]]}]}}


def tempo_payload(*, trace_id=TRACE_ID, route="/api/v1/scenarios/error", status=503, service="hybrid-observability-api"):
    encoded_id = base64.b64encode(bytes.fromhex(trace_id)).decode("ascii")
    return {
        "trace": {
            "resourceSpans": [{
                "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": service}}]},
                "scopeSpans": [{"spans": [{
                    "traceId": encoded_id,
                    "kind": "SPAN_KIND_SERVER",
                    "attributes": [
                        {"key": "http.route", "value": {"stringValue": route}},
                        {"key": "http.status_code", "value": {"intValue": str(status)}},
                    ],
                }]}],
            }],
        }
    }


class ResponseValidationTests(unittest.TestCase):
    def test_accepts_expected_trace_id(self):
        self.assertEqual(trace_id_from_response({"error": "controlled_service_failure", "trace_id": TRACE_ID}), TRACE_ID)

    def test_rejects_missing_zero_and_malformed_id(self):
        for invalid in (None, "0" * 32, "short", "Z" * 32, 123):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                trace_id_from_response({"error": "controlled_service_failure", "trace_id": invalid})

    def test_rejects_unexpected_error(self):
        with self.assertRaises(ValueError):
            trace_id_from_response({"error": "other", "trace_id": TRACE_ID})


class LokiValidationTests(unittest.TestCase):
    def test_accepts_exact_structured_error(self):
        self.assertTrue(loki_has_correlated_error(loki_payload(), TRACE_ID))

    def test_accepts_wrapped_log(self):
        payload = loki_payload()
        row = payload["data"]["result"][0]["values"][0]
        row[1] = json.dumps({"log": row[1] + "\n"})
        self.assertTrue(loki_has_correlated_error(payload, TRACE_ID))

    def test_rejects_mismatched_trace_or_event(self):
        for payload in (
            loki_payload(trace_id=OTHER_ID),
            loki_payload(event="other"),
            loki_payload(path="/other"),
            loki_payload(status=502),
        ):
            with self.subTest(payload=payload):
                self.assertFalse(loki_has_correlated_error(payload, TRACE_ID))

    def test_rejects_unstructured_and_empty_logs(self):
        payload = loki_payload()
        payload["data"]["result"][0]["values"][0][1] = "trace id " + TRACE_ID
        self.assertFalse(loki_has_correlated_error(payload, TRACE_ID))
        self.assertFalse(loki_has_correlated_error({"status": "success", "data": {"result": []}}, TRACE_ID))


class TempoValidationTests(unittest.TestCase):
    def test_accepts_otlp_base64_trace_id(self):
        self.assertTrue(tempo_has_correlated_error(tempo_payload(), TRACE_ID))

    def test_accepts_new_semantic_convention_status(self):
        payload = tempo_payload()
        attrs = payload["trace"]["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["attributes"]
        attrs[1]["key"] = "http.response.status_code"
        self.assertTrue(tempo_has_correlated_error(payload, TRACE_ID))

    def test_rejects_wrong_id_service_route_or_status(self):
        for payload in (
            tempo_payload(trace_id=OTHER_ID),
            tempo_payload(service="other-service"),
            tempo_payload(route="/other"),
            tempo_payload(status=200),
        ):
            with self.subTest(payload=payload):
                self.assertFalse(tempo_has_correlated_error(payload, TRACE_ID))

    def test_rejects_empty_trace_and_wrong_kind(self):
        self.assertFalse(tempo_has_correlated_error({"trace": {"resourceSpans": []}}, TRACE_ID))
        payload = tempo_payload()
        payload["trace"]["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["kind"] = "SPAN_KIND_CLIENT"
        self.assertFalse(tempo_has_correlated_error(payload, TRACE_ID))


if __name__ == "__main__":
    unittest.main()
