from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from common.config import settings


class ServiceAgentDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(pattern=r"^[a-z][a-z0-9_]{2,63}$")
    description: str = Field(min_length=10, max_length=500)
    base_url: HttpUrl
    enabled: bool = True
    capabilities: list[str] = Field(default_factory=list)
    protocols: list[Literal["a2a", "mcp"]] = Field(default_factory=lambda: ["a2a"])
    preferred_protocol: Literal["a2a", "mcp"] = "a2a"
    mcp_url: HttpUrl | None = None
    mcp_tool: str | None = None

    @model_validator(mode="after")
    def validate_protocol_configuration(self) -> ServiceAgentDefinition:
        if self.preferred_protocol not in self.protocols:
            raise ValueError("preferred_protocol must be included in protocols")
        if "mcp" in self.protocols and (self.mcp_url is None or not self.mcp_tool):
            raise ValueError("MCP services require mcp_url and mcp_tool")
        return self


def load_service_agent_definitions(
    path: Path | None = None,
) -> list[ServiceAgentDefinition]:
    registry_path = path or settings.service_registry_path
    if not registry_path.exists():
        raise FileNotFoundError(f"Service-agent registry not found: {registry_path}")

    with registry_path.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    if not isinstance(raw, list):
        raise ValueError("The service-agent registry must contain a JSON list.")

    definitions = [ServiceAgentDefinition.model_validate(item) for item in raw]
    names = [item.name for item in definitions]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"Duplicate service-agent names: {duplicates}")

    return [item for item in definitions if item.enabled]
