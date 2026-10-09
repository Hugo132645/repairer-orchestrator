# Adding a dual-protocol LangGraph service agent

Every specialist is an independent LangGraph application exposed through the
gateway as both an official A2A agent and an MCP tool.

## 1. Create the domain tool

Add a deterministic function under `service_agents/<name>/tools.py`. Validate
inputs with Pydantic and return the shared structured status contract:
`success`, `no_match`, `missing_information`, `invalid_request`,
`temporary_failure`, or `internal_error`.

## 2. Build the LangGraph

For a single-tool specialist:

```python
from common.service_graph import build_service_graph
from service_agents.warranty.tools import lookup_synthetic_warranty

graph = build_service_graph(lookup_synthetic_warranty)
```

Use an explicit `StateGraph` when the service needs multiple nodes.

## 3. Expose the graph through the gateway

```python
from common.a2a_transport import build_a2a_app
from service_agents.warranty.agent import graph

a2a_app = build_a2a_app(
    graph=graph,
    name="warranty_agent",
    description="Checks synthetic warranty demonstration data.",
    base_url="http://127.0.0.1:8004",
    capabilities=["warranty_lookup"],
)
```

Mount the A2A application under `/a2a/<agent_name>` in
`agent_gateway/server.py`, and add an `@mcp.tool` wrapper that invokes the same
graph. The agent card is published below the A2A mount and the tool is available
from `/mcp`.

## 4. Register and route

Add the A2A URL, MCP URL, MCP tool name, supported protocols, and preferred
protocol to `repairer_orchestrator/service_agents.json`. Add its business
capability and structured payload mapping to `repairer_orchestrator/agent.py`.
Extend the semantic validation instructions and routing tests so required fields
are checked before the graph can reach `invoke_services`.

## 5. Verify

- Test domain-tool success, no match, and invalid input.
- Test that validation structurally precedes delegation.
- Test both the A2A card/message round trip and MCP tool invocation.
- Update startup, preflight, health UI, and architecture documentation.
- Run pytest, Ruff, and `scripts/check_services.py`.
