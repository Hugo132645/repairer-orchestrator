from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class ServiceState(TypedDict, total=False):
    request: dict[str, Any]
    result: dict[str, Any]


def build_service_graph(
    handler: Callable[..., dict[str, Any]],
):
    """Build a narrow LangGraph service that validates through its domain tool."""

    def execute(state: ServiceState) -> ServiceState:
        return {"result": handler(**state.get("request", {}))}

    builder = StateGraph(ServiceState)
    builder.add_node("execute_domain_tool", execute)
    builder.add_edge(START, "execute_domain_tool")
    builder.add_edge("execute_domain_tool", END)
    return builder.compile()
