from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import Any

from litellm import acompletion

from common.audit import audit_event
from common.config import settings
from common.usage import usage_store

logger = logging.getLogger(__name__)


def configured_model_name() -> str:
    if settings.llm_provider == "azure_openai_v1":
        return f"openai/{settings.model_name}"
    return (
        settings.model_name
        if settings.model_name.startswith("gemini/")
        else f"gemini/{settings.model_name}"
    )


async def complete_text(messages: list[dict[str, str]]) -> str:
    configured_model = configured_model_name()
    audit_event(
        event_type="llm.requested",
        service_name="repairer_orchestrator",
        outcome="started",
        target=configured_model,
        payload={"message_count": len(messages)},
    )
    started = perf_counter()
    try:
        response = await acompletion(model=configured_model, messages=messages)
    except Exception:
        usage_store.record(
            service_name="repairer_orchestrator",
            provider=settings.llm_provider,
            configured_model=configured_model,
            resolved_model=None,
            status="failure",
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            cost_usd=None,
            cost_source=None,
            latency_ms=round((perf_counter() - started) * 1000, 2),
        )
        raise

    content = response.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("The configured model returned no text.")
    usage = getattr(response, "usage", None)

    def usage_value(name: str) -> int | None:
        value = (
            usage.get(name)
            if isinstance(usage, dict)
            else getattr(usage, name, None)
            if usage is not None
            else None
        )
        return value if isinstance(value, int) else None

    hidden = getattr(response, "_hidden_params", {}) or {}
    response_cost = hidden.get("response_cost") if isinstance(hidden, dict) else None
    cost_usd = float(response_cost) if isinstance(response_cost, int | float) else None
    usage_store.record(
        service_name="repairer_orchestrator",
        provider=settings.llm_provider,
        configured_model=configured_model,
        resolved_model=str(getattr(response, "model", "") or "") or None,
        status="success",
        prompt_tokens=usage_value("prompt_tokens"),
        completion_tokens=usage_value("completion_tokens"),
        total_tokens=usage_value("total_tokens"),
        cost_usd=cost_usd,
        cost_source="litellm_estimate" if cost_usd is not None else None,
        latency_ms=round((perf_counter() - started) * 1000, 2),
    )
    audit_event(
        event_type="llm.completed",
        service_name="repairer_orchestrator",
        outcome="success",
        target="configured_model",
        payload={
            "has_response": True,
            "prompt_tokens": usage_value("prompt_tokens"),
            "completion_tokens": usage_value("completion_tokens"),
            "total_tokens": usage_value("total_tokens"),
            "cost_usd": cost_usd,
            "cost_source": "litellm_estimate" if cost_usd is not None else None,
        },
    )
    return content.strip()


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError("The model response must be a JSON object.")
    return value
