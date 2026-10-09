from __future__ import annotations

from common.service_graph import build_service_graph
from service_agents.parts.tools import search_parts

graph = build_service_graph(search_parts)
