from __future__ import annotations

from common.a2a_transport import build_a2a_app
from common.logging_config import configure_logging
from common.observability import configure_tracing
from service_agents.diagnostics.agent import graph

configure_logging("diagnostics_agent")
configure_tracing("diagnostics_agent")

a2a_app = build_a2a_app(
    graph=graph,
    name="diagnostics_agent",
    description="Interprets synthetic fault codes and proposes non-conclusive checks.",
    base_url="http://127.0.0.1:8002",
    capabilities=["fault_code_interpretation", "diagnostic_checks"],
)
