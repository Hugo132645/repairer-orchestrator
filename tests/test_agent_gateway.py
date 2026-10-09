from __future__ import annotations

from starlette.testclient import TestClient

from agent_gateway.server import app


def test_gateway_exposes_health_and_mounted_a2a_cards() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        card = client.get("/a2a/diagnostics_agent/.well-known/agent-card.json")
        catalog = client.get("/.well-known/agent-catalog.json")
        documentation = client.get("/docs/a2a")

    assert health.status_code == 200
    assert health.json()["protocols"] == ["a2a", "mcp"]
    assert health.json()["mcp_endpoint"].endswith("/mcp")
    assert card.status_code == 200
    assert card.json()["name"] == "diagnostics_agent"
    assert card.json()["url"] == "http://127.0.0.1:8004/a2a/diagnostics_agent/"
    assert card.json()["provider"]["organization"] == "Repairer Desk Prototype"
    assert card.json()["security"] == []
    assert catalog.status_code == 200
    assert len(catalog.json()["agents"]) == 3
    assert documentation.json()["protocol"] == "A2A 0.3.0"
