from __future__ import annotations

from common.a2a_transport import build_a2a_app
from common.logging_config import configure_logging
from common.observability import configure_tracing
from service_agents.parts.agent import graph

configure_logging("parts_agent")
configure_tracing("parts_agent")

a2a_app = build_a2a_app(
    graph=graph,
    name="parts_agent",
    description="Checks a synthetic local parts catalogue for availability.",
    base_url="http://127.0.0.1:8003",
    capabilities=["parts_availability"],
)
