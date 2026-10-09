from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount

from common.a2a_transport import build_a2a_app
from common.logging_config import configure_logging
from common.observability import configure_tracing, instrument_asgi_app
from service_agents.diagnostics.agent import graph as diagnostics_graph
from service_agents.parts.agent import graph as parts_graph
from service_agents.service_library.agent import graph as service_library_graph

SERVICE_NAME = "agent_gateway"
BASE_URL = "http://127.0.0.1:8004"
configure_logging(SERVICE_NAME)
configure_tracing(SERVICE_NAME)

mcp = FastMCP(
    "Synthetic Repair Agent Gateway",
    instructions=(
        "Provides synthetic diagnostic, procedure, and parts tools. "
        "Results never authorize real repairs."
    ),
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
)


async def _invoke(graph: Any, request: dict[str, Any]) -> dict[str, Any]:
    output = await graph.ainvoke({"request": request})
    result = output.get("result", {})
    if not isinstance(result, dict):
        raise RuntimeError("The LangGraph specialist returned an invalid result.")
    return result


@mcp.tool(name="diagnostics_agent")
async def diagnostics_agent(
    fault_codes: list[str],
    symptoms: list[str] | None = None,
) -> dict[str, Any]:
    """Interpret synthetic fault codes without concluding component failure."""

    return await _invoke(
        diagnostics_graph,
        {"fault_codes": fault_codes, "symptoms": symptoms or []},
    )


@mcp.tool(name="service_library_agent")
async def service_library_agent(
    vehicle_model: str,
    fault_codes: list[str],
    market: str = "EU",
) -> dict[str, Any]:
    """Find an exact synthetic repair-procedure catalogue match."""

    return await _invoke(
        service_library_graph,
        {
            "vehicle_model": vehicle_model,
            "fault_codes": fault_codes,
            "market": market,
        },
    )


@mcp.tool(name="parts_agent")
async def parts_agent(
    vehicle_model: str,
    part_name: str,
    market: str = "EU",
) -> dict[str, Any]:
    """Check the synthetic local parts catalogue."""

    return await _invoke(
        parts_graph,
        {
            "vehicle_model": vehicle_model,
            "part_name": part_name,
            "market": market,
        },
    )


async def health(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "available",
            "protocols": ["a2a", "mcp"],
            "agents": [
                "diagnostics_agent",
                "service_library_agent",
                "parts_agent",
            ],
            "mcp_endpoint": f"{BASE_URL}/mcp",
        }
    )


async def agent_catalog(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "catalog_version": "1.0",
            "environment": "local-synthetic-prototype",
            "a2a_protocol_version": "0.3.0",
            "authentication": "none-local-prototype",
            "agents": [
                {
                    "id": name,
                    "card_url": (f"{BASE_URL}/a2a/{name}/.well-known/agent-card.json"),
                    "mcp_tool": name,
                }
                for name in (
                    "diagnostics_agent",
                    "service_library_agent",
                    "parts_agent",
                )
            ],
            "limitations": [
                "Synthetic demonstration data only.",
                "No production identity provider or transport security.",
                "No repair authorization.",
            ],
        }
    )


async def a2a_documentation(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "title": "Repairer Desk Prototype Agent Gateway",
            "protocol": "A2A 0.3.0",
            "transport": "JSON-RPC over HTTP",
            "content_type": "application/json",
            "status_contract": [
                "success",
                "no_match",
                "missing_information",
                "invalid_request",
                "temporary_failure",
                "internal_error",
            ],
            "production_requirements": [
                "TLS",
                "federated workload identity",
                "signed agent cards",
                "authorization scopes",
                "rate limiting",
                "durable task storage",
            ],
        }
    )


def _a2a_mount(
    *,
    name: str,
    description: str,
    graph: Any,
    capabilities: list[str],
) -> Mount:
    path = f"/a2a/{name}"
    return Mount(
        path,
        app=build_a2a_app(
            graph=graph,
            name=name,
            description=description,
            base_url=f"{BASE_URL}{path}/",
            capabilities=capabilities,
        ),
    )


gateway_app = mcp.streamable_http_app()
gateway_app.router.routes.extend(
    [
        _a2a_mount(
            name="diagnostics_agent",
            description="Interprets synthetic fault codes and proposes checks.",
            graph=diagnostics_graph,
            capabilities=["fault_code_interpretation", "diagnostic_checks"],
        ),
        _a2a_mount(
            name="service_library_agent",
            description="Finds synthetic procedures by vehicle, code, and market.",
            graph=service_library_graph,
            capabilities=["repair_procedure_search"],
        ),
        _a2a_mount(
            name="parts_agent",
            description="Checks a synthetic local parts catalogue.",
            graph=parts_graph,
            capabilities=["parts_availability"],
        ),
    ]
)
gateway_app.router.add_route("/health", health, methods=["GET"])
gateway_app.router.add_route("/.well-known/agent-catalog.json", agent_catalog, methods=["GET"])
gateway_app.router.add_route("/docs/a2a", a2a_documentation, methods=["GET"])
app = instrument_asgi_app(gateway_app)
