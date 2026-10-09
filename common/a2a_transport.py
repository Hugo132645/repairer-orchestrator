from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentProvider,
    AgentSkill,
    Message,
    Part,
    Role,
    Task,
    TextPart,
)
from a2a.utils import get_message_text, new_agent_text_message

from common.observability import instrument_asgi_app


class LangGraphAgentExecutor(AgentExecutor):
    def __init__(self, graph: Any) -> None:
        self.graph = graph

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            request = json.loads(context.get_user_input())
            if not isinstance(request, dict):
                raise ValueError("A2A request must be a JSON object.")
            output = await self.graph.ainvoke({"request": request})
            result = output.get("result", {})
        except Exception as exc:
            result = {
                "status": "internal_error",
                "message": f"Service execution failed: {type(exc).__name__}.",
                "data": {},
                "errors": [],
            }
        await event_queue.enqueue_event(
            new_agent_text_message(
                json.dumps(result, ensure_ascii=False),
                context_id=context.context_id,
                task_id=context.task_id,
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancellation is not supported by this prototype.")


def _message_from_client_event(event: Any) -> Message | None:
    """Return the agent response from either valid A2A client event shape."""

    if isinstance(event, Message):
        return event
    if not isinstance(event, tuple) or not event or not isinstance(event[0], Task):
        return None

    task = event[0]
    if task.status.message is not None:
        return task.status.message
    for message in reversed(task.history or []):
        if message.role == Role.agent:
            return message
    return None


def build_a2a_app(
    *,
    graph: Any,
    name: str,
    description: str,
    base_url: str,
    capabilities: list[str],
) -> Any:
    card = AgentCard(
        name=name,
        description=f"{description} Synthetic demonstration only; never authorizes repairs.",
        url=base_url,
        version="1.0.0",
        protocolVersion="0.3.0",
        preferredTransport="JSONRPC",
        provider=AgentProvider(
            organization="Repairer Desk Prototype",
            url="http://127.0.0.1:8004/docs/a2a",
        ),
        documentationUrl="http://127.0.0.1:8004/docs/a2a",
        additionalInterfaces=[
            AgentInterface(url=base_url, transport="JSONRPC"),
        ],
        capabilities=AgentCapabilities(streaming=False),
        defaultInputModes=["application/json", "text/plain"],
        defaultOutputModes=["application/json", "text/plain"],
        security=[],
        supportsAuthenticatedExtendedCard=False,
        skills=[
            AgentSkill(
                id=capability,
                name=capability.replace("_", " ").title(),
                description=f"{description} Returns the shared structured status contract.",
                tags=["synthetic", "repair", capability],
                examples=[f"Invoke {capability.replace('_', ' ')} using synthetic repair data."],
                inputModes=["application/json"],
                outputModes=["application/json"],
            )
            for capability in capabilities
        ],
    )
    handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(graph),
        task_store=InMemoryTaskStore(),
    )
    return instrument_asgi_app(
        A2AStarletteApplication(agent_card=card, http_handler=handler).build()
    )


async def invoke_a2a_agent(
    base_url: str,
    payload: dict[str, Any],
    *,
    timeout: float,
    context_id: str,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        card = await A2ACardResolver(client, base_url).get_agent_card()
        a2a_client = ClientFactory(ClientConfig(streaming=False, httpx_client=client)).create(card)
        message = Message(
            messageId=str(uuid4()),
            contextId=context_id,
            role=Role.user,
            parts=[Part(root=TextPart(text=json.dumps(payload, ensure_ascii=False)))],
        )
        result_message: Message | None = None
        async for event in a2a_client.send_message(message):
            event_message = _message_from_client_event(event)
            if event_message is not None:
                result_message = event_message
    if result_message is None:
        raise RuntimeError("The remote A2A agent did not return a message.")
    result = json.loads(get_message_text(result_message))
    if not isinstance(result, dict):
        raise RuntimeError("The remote A2A response was not a JSON object.")
    return result
