from __future__ import annotations

from pathlib import Path

import pytest

from repairer_orchestrator.registry import load_service_agent_definitions


def test_registry_loads_enabled_agents() -> None:
    definitions = load_service_agent_definitions()
    assert {definition.name for definition in definitions} == {
        "diagnostics_agent",
        "service_library_agent",
        "parts_agent",
    }
    assert all(set(definition.protocols) == {"a2a", "mcp"} for definition in definitions)
    assert {definition.preferred_protocol for definition in definitions} == {"a2a", "mcp"}
    assert all("127.0.0.1:8004" in str(definition.base_url) for definition in definitions)


def test_registry_rejects_duplicate_names() -> None:
    registry = Path(__file__).with_name("data") / "duplicate_service_agents.json"
    with pytest.raises(ValueError, match="Duplicate service-agent names"):
        load_service_agent_definitions(registry)
