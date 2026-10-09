from types import SimpleNamespace

import pytest

from common import llm
from common.usage import LLMUsageStore


def test_azure_openai_v1_uses_openai_compatible_litellm_model(monkeypatch) -> None:
    monkeypatch.setattr(
        llm,
        "settings",
        SimpleNamespace(llm_provider="azure_openai_v1", model_name="gpt-5-1"),
    )

    assert llm.configured_model_name() == "openai/gpt-5-1"


def test_gemini_uses_litellm_provider_prefix(monkeypatch) -> None:
    monkeypatch.setattr(
        llm,
        "settings",
        SimpleNamespace(llm_provider="gemini", model_name="gemini-3.6-flash"),
    )

    assert llm.configured_model_name() == "gemini/gemini-3.6-flash"


@pytest.mark.asyncio
async def test_complete_text_records_usage_without_content(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class Recorder:
        def record(self, **kwargs) -> None:
            captured.update(kwargs)

    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Synthetic reply"))],
        usage=SimpleNamespace(
            prompt_tokens=12,
            completion_tokens=8,
            total_tokens=20,
        ),
        model="resolved-model-version",
        _hidden_params={"response_cost": 0.0042},
    )

    async def fake_completion(**_kwargs):
        return response

    monkeypatch.setattr(llm, "acompletion", fake_completion)
    monkeypatch.setattr(llm, "usage_store", Recorder())

    result = await llm.complete_text([{"role": "user", "content": "not recorded"}])

    assert result == "Synthetic reply"
    assert captured["prompt_tokens"] == 12
    assert captured["completion_tokens"] == 8
    assert captured["total_tokens"] == 20
    assert captured["cost_usd"] == 0.0042
    assert "messages" not in captured


def test_usage_summary_builds_cumulative_token_and_cost_timeline() -> None:
    store = LLMUsageStore(":memory:")
    try:
        for tokens, cost in ((20, 0.004), (30, 0.006)):
            store.record(
                service_name="repairer_orchestrator",
                provider="prototype",
                configured_model="prototype/model",
                resolved_model="model-version",
                status="success",
                prompt_tokens=tokens // 2,
                completion_tokens=tokens // 2,
                total_tokens=tokens,
                cost_usd=cost,
                cost_source="test_estimate",
                latency_ms=100,
            )

        summary = store.summary()

        assert summary["total_tokens"] == 50
        assert summary["cost_usd"] == pytest.approx(0.01)
        assert summary["timeline"][-1]["tokens"] == 50
        assert summary["timeline"][-1]["cost_usd"] == pytest.approx(0.01)
    finally:
        store.close()
