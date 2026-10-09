from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ValidationSummary(BaseModel):
    status: Literal["success", "missing_information", "not_run"]
    validated: bool
    missing_fields: list[str] = Field(default_factory=list)
    ambiguous_fields: list[str] = Field(default_factory=list)
    clarification_fields: list[str] = Field(default_factory=list)
    normalized_request: dict[str, Any] = Field(default_factory=dict)


class ServiceExecution(BaseModel):
    capability: str
    agent_name: str
    protocol: str = "a2a"
    status: str
    called: bool
    message: str


class ChatResult(BaseModel):
    reply: str
    request_id: str
    completion_status: Literal[
        "complete",
        "partial",
        "needs_clarification",
        "validation_not_run",
    ]
    validation: ValidationSummary
    services: list[ServiceExecution] = Field(default_factory=list)
