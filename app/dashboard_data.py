from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], int]:
    """Read complete JSON object lines, counting malformed/partial records."""
    events: list[dict[str, Any]] = []
    malformed = 0
    try:
        with path.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    malformed += 1
                    continue
                if not isinstance(event, dict):
                    malformed += 1
                    continue
                events.append(event)
    except FileNotFoundError:
        return [], 0
    return events, malformed


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _numbers(events: Iterable[dict[str, Any]], field: str) -> list[float]:
    values = []
    for event in events:
        value = event.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.append(float(value))
    return values


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * percentile / 100
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return round(values[lower] + (values[upper] - values[lower]) * (position - lower), 2)


def aggregate_events(
    events: Iterable[dict[str, Any]],
    *,
    time_range_minutes: int = 60,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    cutoff = current - timedelta(minutes=time_range_minutes)
    window = [
        event for event in events
        if (timestamp := _timestamp(event.get("ts"))) is not None
        and cutoff <= timestamp <= current
    ]
    received = [event for event in window if event.get("event") == "request_received"]
    failed = [event for event in window if event.get("event") == "request_failed"]
    responses = [event for event in window if event.get("event") == "response_sent"]
    tool_results = [event for event in window if isinstance(event.get("tool_success"), bool)]
    errors = Counter(str(event.get("error_type", "unknown")) for event in failed)
    cost_by_minute: dict[str, float] = defaultdict(float)
    for event in responses:
        timestamp = _timestamp(event.get("ts"))
        cost = event.get("cost_usd")
        if timestamp and isinstance(cost, (int, float)) and not isinstance(cost, bool):
            key = timestamp.replace(second=0, microsecond=0).isoformat()
            cost_by_minute[key] += float(cost)

    latencies = _numbers(responses, "latency_ms")
    ttft = _numbers(responses, "ttft_ms")
    qualities = _numbers(responses, "quality_score")
    tokens_in = _numbers(responses, "tokens_in")
    tokens_out = _numbers(responses, "tokens_out")
    costs = _numbers(responses, "cost_usd")
    return {
        "window_start": cutoff.isoformat(),
        "window_end": current.isoformat(),
        "latency": {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
            "ttft_p95": _percentile(ttft, 95),
        },
        "traffic": {"count": len(received), "rate_per_minute": round(len(received) / time_range_minutes, 3)},
        "errors": {
            "error_rate_pct": round(len(failed) / len(received) * 100, 2) if received else 0.0,
            "by_type": dict(errors),
            "tool_success_rate_pct": round(
                sum(event["tool_success"] is True for event in tool_results)
                / len(tool_results) * 100, 2
            ) if tool_results else 0.0,
        },
        "cost": {"total": round(sum(costs), 6), "by_minute": dict(sorted(cost_by_minute.items()))},
        "tokens": {"input": int(sum(tokens_in)), "output": int(sum(tokens_out))},
        "quality": {"mean": round(sum(qualities) / len(qualities), 3) if qualities else None},
        "request_count": len(received),
        "response_count": len(responses),
    }
