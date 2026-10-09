from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH

from repairer_orchestrator.registry import load_service_agent_definitions

DISPLAY_NAMES = {
    "diagnostics_agent": "Diagnostics",
    "service_library_agent": "Service library",
    "parts_agent": "Parts inventory",
}


async def get_service_health() -> list[dict[str, Any]]:
    definitions = load_service_agent_definitions()
    async with httpx.AsyncClient(timeout=2.0) as client:
        return await asyncio.gather(
            *[_check_service(client, definition) for definition in definitions]
        )


async def _check_service(client: httpx.AsyncClient, definition: Any) -> dict[str, Any]:
    started = time.perf_counter()
    url = f"{str(definition.base_url).rstrip('/')}{AGENT_CARD_WELL_KNOWN_PATH}"
    try:
        response = await client.get(url)
        response.raise_for_status()
        card = response.json()
        advertised_name = card.get("name")
        status = "available" if advertised_name == definition.name else "degraded"
    except Exception:
        advertised_name = None
        status = "unavailable"

    return {
        "name": definition.name,
        "display_name": DISPLAY_NAMES.get(
            definition.name,
            definition.name.replace("_", " ").title(),
        ),
        "status": status,
        "latency_ms": round((time.perf_counter() - started) * 1000),
        "advertised_name": advertised_name,
        "protocols": definition.protocols,
        "preferred_protocol": definition.preferred_protocol,
    }
