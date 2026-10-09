from __future__ import annotations

from common.a2a_transport import build_a2a_app
from common.logging_config import configure_logging
from common.observability import configure_tracing
from service_agents.service_library.agent import graph

configure_logging("service_library_agent")
configure_tracing("service_library_agent")

a2a_app = build_a2a_app(
    graph=graph,
    name="service_library_agent",
    description="Finds synthetic repair procedures by vehicle, fault code, and market.",
    base_url="http://127.0.0.1:8001",
    capabilities=["repair_procedure_search"],
)
