# CP2 Monitoring, Tracing, and Prompt Design

## Goal

Complete checkpoint CP2 for the Day 13 LLMOps lab: produce readable Langfuse traces, demonstrate prompt versioning and rollback, provide a six-panel dashboard over the JSONL logs, and define an SLO with actionable alerts and runbooks.

## Scope and constraints

- Install the official `langfuse/skills` Langfuse skill using the Codex skill installer and follow its instrumentation guidance.
- Keep the existing FastAPI application and the pinned Langfuse Python SDK (`4.15.6`).
- Use the Langfuse project configured locally through `.env`; never print or commit its credentials.
- Preserve local fallback behavior when Langfuse is unavailable or not configured.
- Do not record raw user messages, prompts, or generated answers in Langfuse. Record scrubbed previews and operational metadata only.
- Dashboard data source is `data/logs.jsonl`; retain the six panel IDs and contract in `config/dashboard.yaml`.
- Do not create or modify an official challenge file or claim CP3 incident evidence.

## Design

### Trace instrumentation

Retain the `day13-agent-request` root trace and `lab-agent-run` agent observation. Add nested observations for retrieval (type `retriever`) and fake model generation (type `generation`). Keep automatic input/output capture disabled for user-facing functions. Set explicit scrubbed inputs and safe outputs, and attach model, prompt name/label/version, token usage, estimated cost, feature, hashed user ID, session ID, environment, and correlation ID. Ensure standalone workload scripts flush Langfuse before exit.

### Prompt versioning

Use the existing `resolve_prompt` integration and project prompt named `day13-chat`. Publish two real versions with `baseline`, `candidate`, and `production` labels. Run the same sample workload against both candidate versions, record the resulting trace IDs, then move `production` back to the baseline version and verify that subsequent traces report the rolled-back version. Never synthesize version metadata in application code.

### Dashboard, SLO, and alerting

Provide a local Streamlit dashboard that reads JSONL safely and implements the existing latency/TTFT, traffic, errors/retrieval success, cost, token, and quality panels. Display the configured 60-minute time range, units, thresholds, and refresh period. Keep the YAML dashboard contract validator-compatible.

Retain the configured primary SLO (99.5% of requests successful within 3 seconds over 28 days; 0.5% error budget). Replace the three alert placeholders with symptom-based latency, error/retrieval, and quality/cost alerts. Each alert must include a measurable condition, duration, severity, owner, Slack channel, and matching runbook section in `docs/alerts.md`.

### Evidence and delivery

Run the app and sample workload to create at least 10 traces in the configured personal Langfuse project. Capture valid evidence for the trace list, waterfall, prompt versions and rollback, and dashboard. Update the CP2-relevant technical results and artifact links in `submission/REPORT.md` without fabricating student or official challenge details. Run the dashboard validator and relevant tests/checks. Commit and push the completed CP2 checkpoint to the configured `origin` only after reviewing the final diff and confirming no `.env`, API key, or raw PII is included.

## Acceptance criteria

1. A Langfuse trace shows the root/agent/retriever/generation hierarchy with correct observation types and safe metadata.
2. At least 10 newly generated traces are visible in the user's configured Langfuse project; correlation IDs connect traces to JSONL logs.
3. Two real prompt versions and the production rollback are demonstrated by traces, without fabricated versions.
4. The dashboard displays all six contract panels from actual `data/logs.jsonl` records.
5. `config/slo.yaml`, `config/alert_rules.yaml`, and `docs/alerts.md` describe the SLO, three complete alerts, and actionable runbooks.
6. CP2 evidence and report links refer to actual artifacts; no official CP3 investigation is invented.
7. `python scripts/validate_dashboard.py` reports 6/6 panels, and the final CP2 commit is pushed to `origin` without secrets or raw PII.

## Out of scope

Implementing or reporting the official CP3 challenge, deploying dashboard infrastructure, changing model providers, or changing the application API.
