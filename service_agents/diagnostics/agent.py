from __future__ import annotations

from common.service_graph import build_service_graph
from service_agents.diagnostics.tools import interpret_fault_codes

graph = build_service_graph(interpret_fault_codes)
