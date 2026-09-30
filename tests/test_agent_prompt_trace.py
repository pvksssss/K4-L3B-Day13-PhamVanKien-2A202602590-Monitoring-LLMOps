from __future__ import annotations

from contextlib import contextmanager

from app import agent as agent_module


class ManagedPrompt:
    version = 3

    def compile(self, **variables: str) -> str:
        return (
            f"Feature={variables['feature']}\n"
            f"Docs={variables['docs']}\n"
            f"Question={variables['message']}"
        )


class RecordingLangfuseClient:
    def __init__(self) -> None:
        self.prompt = ManagedPrompt()
        self.span_updates: list[dict] = []
        self.observations: list[dict] = []

    def get_prompt(self, name: str, **kwargs):
        return self.prompt

    def update_current_span(self, **kwargs) -> None:
        self.span_updates.append(kwargs)

    @contextmanager
    def start_as_current_observation(self, **kwargs):
        observation = {"start": kwargs, "updates": []}
        self.observations.append(observation)

        class Handle:
            def update(self, **update_kwargs):
                observation["updates"].append(update_kwargs)

        try:
            yield Handle()
        except Exception as exc:
            observation["error"] = type(exc).__name__
            raise


def test_agent_records_prompt_version_with_v4_observation_api(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)

    propagated: list[dict] = []

    @contextmanager
    def record_attributes(**kwargs):
        propagated.append(kwargs)
        yield

    monkeypatch.setattr(agent_module, "propagate_attributes", record_attributes)

    agent = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain traces",
        correlation_id="req-12345678",
    )

    span_update = client.span_updates[-1]
    assert span_update["metadata"] == {
        "documentCount": 1,
        "queryPreview": "Explain traces",
        "promptName": "day13-chat",
        "promptLabel": "production",
        "promptVersion": "3",
        "promptSource": "langfuse",
        "promptFetchError": "",
    }
    assert span_update["version"] == "3"
    assert propagated[0]["metadata"]["correlationId"] == "req-12345678"
    assert propagated[-1]["prompt"] is client.prompt


def test_agent_creates_safe_nested_retriever_and_generation_observations(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)

    agent_module.LabAgent.run.__wrapped__(
        agent_module.LabAgent(),
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Contact me at person@example.com about refunds",
        correlation_id="req-12345678",
    )

    assert [item["start"]["as_type"] for item in client.observations] == [
        "retriever",
        "generation",
    ]
    retrieval, generation = client.observations
    assert retrieval["start"]["input"]["query"] == (
        "Contact me at [REDACTED_EMAIL] about refunds"
    )
    assert retrieval["updates"][-1]["output"]["document_count"] == 1
    assert generation["start"]["name"] == "llm.generate"
    assert generation["start"]["model"] == "claude-sonnet-4-5"
    assert "person@example.com" not in str(client.observations)
    generation_update = generation["updates"][-1]
    assert generation_update["usage_details"]["input"] > 0
    assert generation_update["usage_details"]["output"] > 0
    assert generation_update["cost_details"]["total"] > 0


def test_retrieval_failure_is_attached_to_child_observation(monkeypatch) -> None:
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: False)

    def fail_retrieval(_message: str) -> list[str]:
        raise RuntimeError("Vector store timeout")

    monkeypatch.setattr(agent_module, "retrieve", fail_retrieval)

    try:
        agent_module.LabAgent.run.__wrapped__(
            agent_module.LabAgent(),
            user_id="student-01",
            feature="qa",
            session_id="session-01",
            message="Explain tracing",
            correlation_id="req-12345678",
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("retrieval error should propagate to the caller")

    assert len(client.observations) == 1
    assert client.observations[0]["start"]["as_type"] == "retriever"
    assert client.observations[0]["error"] == "RuntimeError"
