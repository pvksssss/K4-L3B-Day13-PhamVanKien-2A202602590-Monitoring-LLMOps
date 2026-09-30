from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx

from app import logging_config
from app.main import app


def _post_chat(headers: dict[str, str]) -> httpx.Response:

    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/chat",
                headers=headers,
                json={
                    "user_id": "student-01",
                    "session_id": "session-01",
                    "feature": "qa",
                    "message": "Email student@example.com and phone 0901234567; CCCD 012345678901; card 4111 1111 1111 1111",
                },
            )

    return asyncio.run(send())


def test_supplied_request_id_is_returned_and_bound_to_enriched_scrubbed_logs(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    response = _post_chat({"x-request-id": "req-a1b2c3d4"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-a1b2c3d4"
    assert response.headers["x-response-time-ms"].isdigit()
    assert response.json()["correlation_id"] == "req-a1b2c3d4"

    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    api_records = [record for record in records if record.get("service") == "api"]
    assert {record["correlation_id"] for record in api_records} == {"req-a1b2c3d4"}
    for record in api_records:
        assert record["user_id_hash"] == "2a2006df8771"
        assert record["session_id"] == "session-01"
        assert record["feature"] == "qa"
        assert record["model"] == "claude-sonnet-4-5"
        assert record["env"] == "test"

    serialized = log_path.read_text(encoding="utf-8")
    for raw_value in ("student@example.com", "0901234567", "012345678901", "4111 1111 1111 1111"):
        assert raw_value not in serialized


def test_missing_or_invalid_request_id_is_generated(monkeypatch, tmp_path: Path) -> None:
    for headers in ({}, {"x-request-id": "not-a-request-id"}):
        log_path = tmp_path / f"{len(headers)}.jsonl"
        monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
        response = _post_chat(headers)
        correlation_id = response.headers["x-request-id"]
        assert re.fullmatch(r"req-[0-9a-f]{8}", correlation_id)
        assert response.json()["correlation_id"] == correlation_id
