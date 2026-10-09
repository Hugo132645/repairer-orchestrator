from __future__ import annotations

from common.service_graph import build_service_graph
from service_agents.service_library.tools import search_repair_procedures

graph = build_service_graph(search_repair_procedures)
