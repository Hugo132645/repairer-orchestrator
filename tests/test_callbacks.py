from __future__ import annotations

import json

import pytest

from common.progress import capture_progress
from repairer_orchestrator.agent import build_orchestrator_graph


@pytest.mark.asyncio
async def test_graph_blocks_remote_services_when_validation_fails() -> None:
    calls: list[str] = []
    model_responses = iter(
        [
            json.dumps(
                {
                    "vehicle_model": None,
                    "fault_codes": [],
                    "part_name": None,
                    "market": "EU",
                    "requested_capabilities": ["diagnostics"],
                    "ambiguous_fields": [],
                }
            ),
            json.dumps(
                {
                    "validated": False,
                    "missing_fields": ["fault_codes"],
                    "ambiguous_fields": [],
                    "clarification_fields": ["fault_codes"],
                    "normalized_request": {
                        "vehicle_model": None,
                        "fault_codes": [],
                        "part_name": None,
                        "market": "EU",
                        "requested_capabilities": ["diagnostics"],
                    },
                }
            ),
            "Please provide the fault code.",
        ]
    )

    async def model_call(_):
        return next(model_responses)

    async def service_call(base_url, payload, **_):
        calls.append(base_url)
        return {"status": "success", "message": "unexpected", "data": payload}

    graph = build_orchestrator_graph(model_call=model_call, service_call=service_call)
    output = await graph.ainvoke(
        {
            "request_text": "Diagnose the warning light.",
            "request_id": "request-1",
            "language": "English",
            "history": [],
        }
    )

    assert output["validation"]["status"] == "missing_information"
    assert calls == []


@pytest.mark.asyncio
async def test_programmatic_guard_blocks_incomplete_model_approval() -> None:
    calls: list[str] = []
    model_responses = iter(
        [
            json.dumps(
                {
                    "vehicle_model": "Demo Compact Hatchback",
                    "fault_codes": [],
                    "part_name": None,
                    "market": "EU",
                    "requested_capabilities": ["diagnostics"],
                    "ambiguous_fields": [],
                }
            ),
            json.dumps(
                {
                    "validated": True,
                    "missing_fields": [],
                    "ambiguous_fields": [],
                    "clarification_fields": [],
                    "normalized_request": {
                        "vehicle_model": "Demo Compact Hatchback",
                        "fault_codes": [],
                        "part_name": None,
                        "market": "EU",
                        "requested_capabilities": ["diagnostics"],
                    },
                }
            ),
            "Please provide the diagnostic trouble code.",
        ]
    )

    async def model_call(_):
        return next(model_responses)

    async def service_call(base_url, _payload, **_):
        calls.append(base_url)
        return {"status": "success", "message": "unexpected", "data": {}}

    graph = build_orchestrator_graph(model_call=model_call, service_call=service_call)
    output = await graph.ainvoke(
        {
            "request_text": "Diagnose this vehicle.",
            "request_id": "request-programmatic-guard",
            "language": "English",
            "history": [],
        }
    )

    assert output["validation"]["data"]["validated"] is False
    assert output["validation"]["data"]["missing_fields"] == ["fault_codes"]
    assert calls == []


@pytest.mark.asyncio
async def test_graph_calls_service_only_after_successful_validation() -> None:
    calls: list[str] = []
    progress_events: list[dict[str, object]] = []
    model_responses = iter(
        [
            json.dumps(
                {
                    "vehicle_model": "Demo Vehicle A",
                    "fault_codes": ["P0301"],
                    "part_name": None,
                    "market": "EU",
                    "requested_capabilities": ["diagnostics"],
                    "ambiguous_fields": [],
                }
            ),
            json.dumps(
                {
                    "validated": True,
                    "missing_fields": [],
                    "ambiguous_fields": [],
                    "clarification_fields": [],
                    "normalized_request": {
                        "vehicle_model": "Demo Vehicle A",
                        "fault_codes": ["P0301"],
                        "part_name": None,
                        "market": "EU",
                        "requested_capabilities": ["diagnostics"],
                    },
                }
            ),
            "Synthetic result.",
        ]
    )

    async def model_call(_):
        return next(model_responses)

    async def service_call(base_url, payload, **_):
        calls.append(base_url)
        return {"status": "success", "message": "ok", "data": payload}

    graph = build_orchestrator_graph(model_call=model_call, service_call=service_call)
    with capture_progress(progress_events.append):
        output = await graph.ainvoke(
            {
                "request_text": "Assess P0301.",
                "request_id": "request-2",
                "language": "English",
                "history": [],
            }
        )

    assert output["validation"]["status"] == "success"
    assert calls == ["http://127.0.0.1:8004/a2a/diagnostics_agent"]
    assert output["service_results"]["diagnostics"]["_protocol"] == "a2a"
    assert [event["event"] for event in progress_events] == [
        "extracting_request",
        "extraction_completed",
        "validating_request",
        "validation_completed",
        "routing_completed",
        "agent_started",
        "agent_completed",
        "consolidating_results",
        "response_completed",
    ]
    assert progress_events[5]["agent_name"] == "diagnostics_agent"
    assert progress_events[6]["status"] == "success"


@pytest.mark.asyncio
async def test_graph_dispatches_mcp_service_through_gateway() -> None:
    a2a_calls: list[str] = []
    mcp_calls: list[tuple[str, str]] = []
    model_responses = iter(
        [
            json.dumps(
                {
                    "vehicle_model": "Demo Vehicle A",
                    "fault_codes": ["P0301"],
                    "part_name": None,
                    "market": "EU",
                    "requested_capabilities": ["service_library"],
                    "ambiguous_fields": [],
                }
            ),
            json.dumps(
                {
                    "validated": True,
                    "missing_fields": [],
                    "ambiguous_fields": [],
                    "clarification_fields": [],
                    "normalized_request": {
                        "vehicle_model": "Demo Vehicle A",
                        "fault_codes": ["P0301"],
                        "part_name": None,
                        "market": "EU",
                        "requested_capabilities": ["service_library"],
                    },
                }
            ),
            "Synthetic procedure result.",
        ]
    )

    async def model_call(_):
        return next(model_responses)

    async def service_call(base_url, *_args, **_kwargs):
        a2a_calls.append(base_url)
        return {"status": "success"}

    async def mcp_call(endpoint, tool_name, payload, **_):
        mcp_calls.append((endpoint, tool_name))
        return {"status": "success", "message": "ok", "data": payload}

    graph = build_orchestrator_graph(
        model_call=model_call,
        service_call=service_call,
        mcp_call=mcp_call,
    )
    output = await graph.ainvoke(
        {
            "request_text": "Find the P0301 procedure for Demo Vehicle A.",
            "request_id": "request-mcp",
            "language": "English",
            "history": [],
        }
    )

    assert output["service_results"]["service_library"]["status"] == "success"
    assert output["service_results"]["service_library"]["_protocol"] == "mcp"
    assert a2a_calls == []
    assert mcp_calls == [("http://127.0.0.1:8004/mcp", "service_library_agent")]


@pytest.mark.asyncio
async def test_semantic_validator_resolves_stale_extraction_ambiguity() -> None:
    model_responses = iter(
        [
            json.dumps(
                {
                    "vehicle_model": "Demo Vehicle A",
                    "fault_codes": ["P0301"],
                    "part_name": None,
                    "market": "EU",
                    "requested_capabilities": ["diagnostics"],
                    "ambiguous_fields": ["vehicle_model"],
                }
            ),
            json.dumps(
                {
                    "validated": True,
                    "missing_fields": [],
                    "ambiguous_fields": [],
                    "clarification_fields": [],
                    "normalized_request": {
                        "vehicle_model": "Demo Vehicle A",
                        "fault_codes": ["P0301"],
                        "part_name": None,
                        "market": "EU",
                        "requested_capabilities": ["diagnostics"],
                    },
                }
            ),
            "Synthetic result.",
        ]
    )

    async def model_call(_):
        return next(model_responses)

    async def service_call(_base_url, _payload, **_):
        return {"status": "success", "message": "ok", "data": {}}

    graph = build_orchestrator_graph(
        model_call=model_call,
        service_call=service_call,
    )
    output = await graph.ainvoke(
        {
            "request_text": "The vehicle is exactly Demo Vehicle A. Assess P0301.",
            "request_id": "request-semantic-validation",
            "language": "English",
            "history": [],
        }
    )

    assert output["validation"]["status"] == "success"
    assert output["validation"]["data"]["ambiguous_fields"] == []
