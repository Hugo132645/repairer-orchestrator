from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ToolError(StrictModel):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ToolResponse(StrictModel):
    status: Literal[
        "success",
        "no_match",
        "missing_information",
        "invalid_request",
        "temporary_failure",
        "internal_error",
    ]
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[ToolError] = Field(default_factory=list)


class RepairProcedureQuery(StrictModel):
    vehicle_model: str = Field(min_length=1, max_length=100)
    fault_codes: list[str] = Field(min_length=1, max_length=20)
    market: str = Field(default="EU", min_length=2, max_length=20)

    @field_validator("fault_codes")
    @classmethod
    def normalize_fault_codes(cls, value: list[str]) -> list[str]:
        return [code.strip().upper() for code in value if code.strip()]


class DiagnosticQuery(StrictModel):
    fault_codes: list[str] = Field(min_length=1, max_length=20)
    symptoms: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("fault_codes")
    @classmethod
    def normalize_fault_codes(cls, value: list[str]) -> list[str]:
        return [code.strip().upper() for code in value if code.strip()]


class PartsQuery(StrictModel):
    vehicle_model: str = Field(min_length=1, max_length=100)
    part_name: str = Field(min_length=1, max_length=100)
    market: str = Field(default="EU", min_length=2, max_length=20)
