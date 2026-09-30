# CP2 Monitoring Implementation Plan

> **For agentic workers:** Execute this plan inline with `superpowers:executing-plans`.

**Goal:** Complete CP2 with Langfuse trace hierarchy, real prompt version/rollback evidence, a six-panel dashboard, SLO and alerts, then commit and push the checkpoint.

**Architecture:** Keep FastAPI and the pinned Langfuse SDK. Instrument the existing agent pipeline with nested observations and PII-safe fields; add a local Streamlit dashboard over the existing JSONL event log; finish the existing YAML operational contracts and runbooks. Use the configured personal Langfuse project for real prompt changes and generated traces.

**Tech Stack:** Python 3.11+, FastAPI, Langfuse Python SDK 4.15.6, Streamlit, Plotly, PyYAML, pytest.

**Spec:** `docs/superpowers/specs/2026-09-30-cp2-monitoring-design.md`

## Global Constraints

- Keep `langfuse==4.15.6` and existing FastAPI contracts.
- Read and use the official `langfuse/skills` instrumentation reference.
- Never expose `.env` values or commit credentials, raw PII, or `config/challenge.json`.
- Keep Langfuse optional at runtime and keep automatic raw input/output capture disabled.
- Preserve the six panel IDs and 60-minute/30-second dashboard contract.
- Ask the user before capturing any screenshot; do not use screenshots without permission.
- Push only after CP2 evidence, validators, report, and final diff pass review.

## Review Focus

- Tracing disabled or client unavailable: chat still works and local fallback is explicit.
- User inputs containing email, phone, CCCD, or payment-card data: logs and trace previews contain redacted values only.
- Failed retrieval or generation: observations close with an error and preserve the request correlation ID.
- Empty, malformed, or partially written JSONL: dashboard renders a useful empty/error state without crashing.
- Prompt fetch fallback and label rollback: trace metadata reflects the actual managed version or clearly says local fallback.

---

### Task 1: Install and consult the Langfuse skill

**Files:** Install official skill to the Codex skills directory; no repository source changes.

- [ ] Use the provided skill-installer helper for `langfuse/skills`, path `skills/langfuse`; inspect helper options first.
- [ ] Read the installed skill and its instrumentation reference, plus current Langfuse best-practices and Python SDK v4 documentation.
- [ ] Record the applicable observation APIs and safe-data guidance for the tracing task.

### Task 2: Instrument nested Langfuse observations

**Files:**
- Modify: `app/agent.py`, `app/mock_rag.py`, `app/mock_llm.py`, `app/tracing.py`
- Modify: `scripts/load_test.py`
- Test: `tests/test_agent_prompt_trace.py`, `tests/test_tracing_adapter.py`; add focused tests only where existing coverage cannot assert the CP2 contract.

**Interfaces:** Agent continues to call `retrieve(message)` and `FakeLLM.generate(prompt)` and returns the current `AgentResult` contract. Tracing wrappers remain no-op-safe when credentials are absent.

- [ ] Pin expected trace shape and safe fields in focused tests; run them to observe the missing child observations.
- [ ] Add a `retriever` child observation around retrieval and a `generation` child around fake generation, nested under the existing agent observation.
- [ ] Explicitly set scrubbed previews rather than capturing function arguments; attach actual model, token usage, estimated cost, and resolved prompt name/label/version.
- [ ] Preserve correlation ID, hashed user ID, session ID, feature, and environment on the trace.
- [ ] Ensure load-test process flushes the Langfuse client after requests complete.
- [ ] Run focused tests, then the full existing pytest suite.

### Task 3: Build the six-panel local dashboard

**Files:**
- Create: `app/dashboard.py` or a root `dashboard.py` Streamlit entrypoint and a focused JSONL aggregation module under `app/`
- Modify: `requirements.txt`, `docs/DASHBOARD_SETUP.md`
- Test: add focused parser/aggregation coverage under `tests/`.

**Interfaces:** Dashboard reads `data/logs.jsonl` and `config/dashboard.yaml`; it does not call external services.

- [ ] Define expected aggregation behavior for empty and malformed JSONL input and run the focused test before implementation.
- [ ] Implement robust JSONL parsing and aggregations for all six required panel IDs.
- [ ] Render latency P50/P95/P99 and TTFT P95, request traffic, error/retrieval success, cost, input/output tokens, and quality.
- [ ] Display the configured time range, units, thresholds, and refresh interval; handle a missing log file gracefully.
- [ ] Add only the runtime dependencies required for Streamlit and charts.
- [ ] Run focused dashboard tests and `python scripts/validate_dashboard.py`.

### Task 4: Complete SLO, alerts, and runbooks

**Files:** Modify `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md`; add/update config tests if needed.

- [ ] Replace all three alert placeholders with measurable symptom-based conditions, duration, severity, owner, Slack channel, and runbook anchors.
- [ ] Align alert thresholds with the configured 99.5%/3-second SLO and guardrails; explain the 0.5% error budget.
- [ ] Write a practical investigation and mitigation runbook for each alert, following metrics → logs → traces.
- [ ] Run relevant configuration tests and dashboard validator.

### Task 5: Create real prompt versions, traces, and CP2 evidence

**Files:** Modify `submission/REPORT.md`; create permitted evidence files under `submission/evidence/` only after user approval for screenshots.

- [ ] Use Langfuse CLI/API guidance from the installed skill to inspect the configured personal project and create/confirm `day13-chat` versions and labels `baseline`, `candidate`, and `production`.
- [ ] Run the same sample workload against baseline and candidate, recording actual trace IDs and verifying actual prompt version metadata.
- [ ] Promote `production` to candidate, create a trace using it, roll `production` back to baseline, then create a trace confirming the rollback.
- [ ] Run at least 10 requests with the app configured for Langfuse; fetch and audit the created traces against current Langfuse best practices.
- [ ] Ask the user before taking screenshots. If permission is not granted, leave screenshot-based evidence pending and do not claim CP2 evidence complete.
- [ ] Update only CP2 report fields with observed results and valid artifact paths; do not invent learner details or CP3 challenge data.
- [ ] Run full pytest, both validators, and a final secret/PII/diff audit. Commit and push CP2 to `origin` only when acceptance criteria are met.

## Completion check

- Langfuse contains at least 10 new traces with readable root/agent/retriever/generation hierarchy and safe metadata.
- Actual prompt versions and production rollback are evidenced by trace metadata.
- Dashboard renders all six contract panels from JSONL data.
- SLO, all alert rules, and runbooks are complete.
- User-approved evidence and report refer to actual runs.
- Tests and validators pass; final commit is pushed without secrets, raw PII, or official challenge data.
