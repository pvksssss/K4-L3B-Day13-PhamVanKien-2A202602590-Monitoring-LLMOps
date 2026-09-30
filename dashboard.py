from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.dashboard_data import aggregate_events, read_jsonl

CONFIG_PATH = ROOT / "config" / "dashboard.yaml"
LOG_PATH = ROOT / "data" / "logs.jsonl"

st.set_page_config(page_title="Day 13 Monitoring & LLMOps", layout="wide")
config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
st.title(config["title"])
st.caption(
    f"Cửa sổ {config['time_range_minutes']} phút · Tự làm mới mỗi "
    f"{config['refresh_seconds']} giây · Nguồn `{LOG_PATH.relative_to(ROOT)}`"
)


def render_dashboard() -> None:
    events, malformed = read_jsonl(LOG_PATH)
    metrics = aggregate_events(events, time_range_minutes=config["time_range_minutes"])
    if malformed:
        st.warning(f"Bỏ qua {malformed} dòng JSONL lỗi hoặc ghi chưa hoàn tất.")
    if not events:
        st.info("Chưa có log. Chạy API và scripts/load_test.py để tạo dữ liệu.")

    panels = {panel["id"]: panel for panel in config["panels"]}
    first, second, third = st.columns(3)
    with first:
        panel = panels["latency"]
        st.subheader(panel["title"])
        cols = st.columns(4)
        for col, key, label in zip(cols, ("p50", "p95", "p99", "ttft_p95"),
                                   ("P50", "P95", "P99", "TTFT P95")):
            with col:
                value = metrics["latency"][key]
                st.metric(label, "—" if value is None else f"{value:.0f} ms")
        st.caption(f"Threshold: P95 ≤ {panel['threshold']['value']} {panel['unit']}")
    with second:
        panel = panels["traffic"]
        st.subheader(panel["title"])
        st.metric("Requests trong cửa sổ", metrics["traffic"]["count"])
        st.metric("Requests/phút", f"{metrics['traffic']['rate_per_minute']:.3f}")
        st.caption(f"Threshold: rate ≥ {panel['threshold']['value']} {panel['unit']}")
    with third:
        panel = panels["errors"]
        st.subheader(panel["title"])
        st.metric("Error rate", f"{metrics['errors']['error_rate_pct']:.2f}%")
        st.metric("Retrieval success", f"{metrics['errors']['tool_success_rate_pct']:.2f}%")
        st.write("Breakdown:", metrics["errors"]["by_type"] or "Không có lỗi")
        st.caption(f"Threshold: error rate ≤ {panel['threshold']['value']} {panel['unit']}")

    fourth, fifth, sixth = st.columns(3)
    with fourth:
        panel = panels["cost"]
        st.subheader(panel["title"])
        st.metric("Tổng chi phí", f"${metrics['cost']['total']:.6f}")
        by_minute = metrics["cost"]["by_minute"]
        if by_minute:
            st.line_chart({"USD/phút": by_minute})
        st.caption(f"Threshold: total ≤ ${panel['threshold']['value']}")
    with fifth:
        panel = panels["tokens"]
        st.subheader(panel["title"])
        st.metric("Input tokens", f"{metrics['tokens']['input']:,}")
        st.metric("Output tokens", f"{metrics['tokens']['output']:,}")
        st.caption(f"Threshold: {panel['threshold']['aggregation']} ≤ {panel['threshold']['value']} tokens")
    with sixth:
        panel = panels["quality"]
        st.subheader(panel["title"])
        mean = metrics["quality"]["mean"]
        st.metric("Quality trung bình", "—" if mean is None else f"{mean:.3f} / 1.0")
        st.caption(f"Threshold: mean ≥ {panel['threshold']['value']} {panel['unit']}")


render_dashboard = st.fragment(run_every=config["refresh_seconds"])(render_dashboard)
render_dashboard()
