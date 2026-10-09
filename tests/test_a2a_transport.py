from __future__ import annotations

import json
from uuid import uuid4

import httpx
import pytest
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import (
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from a2a.utils import get_message_text
from starlette.applications import Starlette
from starlette.routing import Mount

from common.a2a_transport import (
    _message_from_client_event,
    build_a2a_app,
)
from common.service_graph import build_service_graph
from service_agents.diagnostics.tools import interpret_fault_codes


@pytest.mark.asyncio
async def test_langgraph_service_round_trips_through_a2a() -> None:
    app = build_a2a_app(
        graph=build_service_graph(interpret_fault_codes),
        name="diagnostics_agent",
        description="Interprets synthetic fault codes for demonstration.",
        base_url="http://test",
        capabilities=["fault_code_interpretation"],
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        card = await A2ACardResolver(client, "http://test").get_agent_card()
        a2a_client = ClientFactory(ClientConfig(streaming=False, httpx_client=client)).create(card)
        result_message = None
        async for event in a2a_client.send_message(
            Message(
                messageId=str(uuid4()),
                role=Role.user,
                parts=[
                    Part(root=TextPart(text=json.dumps({"fault_codes": ["P0301"], "symptoms": []})))
                ],
            )
        ):
            if isinstance(event, Message):
                result_message = event

    assert card.name == "diagnostics_agent"
    assert isinstance(result_message, Message)
    result = json.loads(get_message_text(result_message))
    assert result["status"] == "success"
    assert result["data"]["results"][0]["fault_code"] == "P0301"


def test_a2a_task_event_exposes_agent_response_message() -> None:
    response = Message(
        messageId=str(uuid4()),
        contextId="portal-request",
        taskId="task-1",
        role=Role.agent,
        parts=[
            Part(
                root=TextPart(
                    text=json.dumps(
                        {"status": "success", "message": "Synthetic result.", "data": {}}
                    )
                )
            )
        ],
    )
    task = Task(
        id="task-1",
        contextId="portal-request",
        status=TaskStatus(state=TaskState.completed, message=response),
        history=[],
    )

    result_message = _message_from_client_event((task, None))

    assert isinstance(result_message, Message)
    result = json.loads(get_message_text(result_message))
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_mounted_a2a_agent_round_trips_using_advertised_url() -> None:
    mounted_app = Starlette(
        routes=[
            Mount(
                "/a2a/diagnostics_agent",
                app=build_a2a_app(
                    graph=build_service_graph(interpret_fault_codes),
                    name="diagnostics_agent",
                    description="Interprets synthetic fault codes.",
                    base_url="http://test/a2a/diagnostics_agent/",
                    capabilities=["fault_code_interpretation"],
                ),
            )
        ]
    )
    transport = httpx.ASGITransport(app=mounted_app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        card = await A2ACardResolver(client, "http://test/a2a/diagnostics_agent").get_agent_card()
        a2a_client = ClientFactory(ClientConfig(streaming=False, httpx_client=client)).create(card)
        result_message = None
        request = Message(
            messageId=str(uuid4()),
            contextId="portal-request",
            role=Role.user,
            parts=[
                Part(root=TextPart(text=json.dumps({"fault_codes": ["P0301"], "symptoms": []})))
            ],
        )
        async for event in a2a_client.send_message(request):
            result_message = _message_from_client_event(event)

    assert card.url == "http://test/a2a/diagnostics_agent/"
    assert isinstance(result_message, Message)
    assert json.loads(get_message_text(result_message))["status"] == "success"
