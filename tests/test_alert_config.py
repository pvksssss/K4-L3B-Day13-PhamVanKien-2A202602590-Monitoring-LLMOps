from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_alert_rules_are_complete_and_point_to_runbooks() -> None:
    rules = yaml.safe_load((ROOT / "config" / "alert_rules.yaml").read_text(encoding="utf-8"))
    runbooks = (ROOT / "docs" / "alerts.md").read_text(encoding="utf-8")

    alerts = rules["alerts"]
    assert [alert["name"] for alert in alerts] == [
        "HighLatencyP95",
        "RequestOrRetrievalFailures",
        "QualityOrCostGuardrail",
    ]
    for index, alert in enumerate(alerts, start=1):
        assert alert["severity"] in {"warning", "critical"}
        assert alert["condition"] and "TODO" not in alert["condition"]
        assert alert["duration"]
        assert alert["type"] == "symptom-based"
        assert alert["channel"].startswith("#")
        assert alert["owner"]
        assert alert["runbook"] == f"docs/alerts.md#alert-{index}"
        assert f"## Alert {index} —" in runbooks


def test_primary_slo_keeps_99_5_percent_target_and_half_percent_budget() -> None:
    slo = yaml.safe_load((ROOT / "config" / "slo.yaml").read_text(encoding="utf-8"))

    assert slo["primary_slo"]["window"] == "28d"
    assert slo["primary_slo"]["target_percent"] == 99.5
    assert slo["primary_slo"]["error_budget_percent"] == 0.5
