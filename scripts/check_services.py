from __future__ import annotations

import asyncio
import json

import httpx
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from repairer_orchestrator.registry import load_service_agent_definitions


async def check_agent(
    client: httpx.AsyncClient,
    name: str,
    base_url: str,
) -> dict[str, object]:
    url = f"{base_url.rstrip('/')}{AGENT_CARD_WELL_KNOWN_PATH}"
    try:
        response = await client.get(url)
        response.raise_for_status()
        card = response.json()
        return {
            "name": name,
            "status": "available",
            "url": url,
            "advertised_name": card.get("name"),
        }
    except Exception as exc:
        return {
            "name": name,
            "status": "unavailable",
            "url": url,
            "error": type(exc).__name__,
        }


async def main() -> None:
    definitions = load_service_agent_definitions()
    async with httpx.AsyncClient(timeout=5.0) as client:
        results = await asyncio.gather(
            *[
                check_agent(client, definition.name, str(definition.base_url))
                for definition in definitions
            ]
        )
    mcp_endpoint = next(
        (str(item.mcp_url) for item in definitions if item.mcp_url is not None),
        None,
    )
    if mcp_endpoint:
        try:
            async with streamablehttp_client(mcp_endpoint) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
            available_tools = {tool.name for tool in tools.tools}
            expected_tools = {item.mcp_tool for item in definitions if item.mcp_tool}
            results.append(
                {
                    "name": "agent_gateway_mcp",
                    "status": (
                        "available" if expected_tools.issubset(available_tools) else "degraded"
                    ),
                    "url": mcp_endpoint,
                    "tools": sorted(available_tools),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "name": "agent_gateway_mcp",
                    "status": "unavailable",
                    "url": mcp_endpoint,
                    "error": type(exc).__name__,
                }
            )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
