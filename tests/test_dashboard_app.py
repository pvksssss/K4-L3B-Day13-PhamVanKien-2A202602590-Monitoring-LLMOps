from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_latency_panel_renders_all_percentiles_and_ttft() -> None:
    app = AppTest.from_file(str(ROOT / "dashboard.py")).run()

    assert not app.exception
    labels = [metric.label for metric in app.metric]
    assert all(label in labels for label in ("P50", "P95", "P99", "TTFT P95"))
