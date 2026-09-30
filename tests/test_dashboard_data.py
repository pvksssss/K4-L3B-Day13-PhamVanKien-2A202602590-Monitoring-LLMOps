from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.dashboard_data import aggregate_events, read_jsonl


def test_jsonl_reader_skips_malformed_and_non_object_lines(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text('{"event":"request_received"}\n{bad json}\n[]\n', encoding="utf-8")

    events, malformed = read_jsonl(path)

    assert events == [{"event": "request_received"}]
    assert malformed == 2


def test_jsonl_reader_handles_missing_file(tmp_path) -> None:
    assert read_jsonl(tmp_path / "missing.jsonl") == ([], 0)


def test_aggregates_all_contract_panels_and_respects_time_window() -> None:
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(minutes=2)).isoformat()
    old = (now - timedelta(hours=2)).isoformat()
    events = [
        {"ts": recent, "event": "request_received"},
        {"ts": recent, "event": "response_sent", "latency_ms": 100,
         "ttft_ms": 40, "cost_usd": 0.2, "tokens_in": 10,
         "tokens_out": 20, "quality_score": 0.8, "tool_success": True},
        {"ts": recent, "event": "request_received"},
        {"ts": recent, "event": "request_failed", "error_type": "RuntimeError",
         "tool_success": False},
        {"ts": old, "event": "response_sent", "latency_ms": 9999,
         "ttft_ms": 9000, "cost_usd": 9, "tokens_in": 900,
         "tokens_out": 900, "quality_score": 0.1},
    ]

    result = aggregate_events(events, time_range_minutes=60, now=now)

    assert result["latency"] == {"p50": 100.0, "p95": 100.0, "p99": 100.0, "ttft_p95": 40.0}
    assert result["traffic"]["count"] == 2
    assert result["errors"]["error_rate_pct"] == 50.0
    assert result["errors"]["tool_success_rate_pct"] == 50.0
    assert result["cost"]["total"] == 0.2
    assert result["tokens"] == {"input": 10, "output": 20}
    assert result["quality"]["mean"] == 0.8
