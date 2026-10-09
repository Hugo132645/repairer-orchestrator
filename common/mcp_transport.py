from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent


async def invoke_mcp_tool(
    endpoint: str,
    tool_name: str,
    payload: dict[str, Any],
    *,
    timeout: float,
) -> dict[str, Any]:
    async with streamablehttp_client(
        endpoint,
        timeout=timedelta(seconds=timeout),
        sse_read_timeout=timedelta(seconds=timeout),
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, payload)

    if result.isError:
        raise RuntimeError(f"MCP tool {tool_name} returned an error.")
    if isinstance(result.structuredContent, dict):
        value = result.structuredContent
    else:
        text = "\n".join(item.text for item in result.content if isinstance(item, TextContent))
        value = json.loads(text)
    if not isinstance(value, dict):
        raise RuntimeError("The MCP tool response was not a JSON object.")
    return value
