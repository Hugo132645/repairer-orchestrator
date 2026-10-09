from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from common.schemas import DiagnosticQuery, ToolError, ToolResponse
from common.tooling import observed_tool

SERVICE_NAME = "diagnostics_agent"

SYNTHETIC_RULES: dict[str, dict[str, Any]] = {
    "P0301": {
        "summary": "Synthetic cylinder-one misfire indication",
        "system": "Synthetic engine ignition",
        "confidence": "demonstration_only",
        "checks": [
            "Inspect the synthetic ignition-coil connection.",
            "Inspect the synthetic spark plug.",
            "Review the synthetic injector connection.",
            "Consider a synthetic compression comparison if prior checks pass.",
        ],
    },
    "P0420": {
        "summary": "Synthetic catalyst-efficiency indication",
        "system": "Synthetic emissions system",
        "confidence": "demonstration_only",
        "checks": [
            "Inspect the synthetic exhaust path for leaks.",
            "Review synthetic oxygen-sensor patterns.",
            "Confirm that no synthetic misfire code remains unresolved.",
        ],
    },
}


@observed_tool(SERVICE_NAME, "interpret_fault_codes")
def interpret_fault_codes(
    fault_codes: list[str],
    symptoms: list[str] | None = None,
) -> dict[str, Any]:
    """Interpret synthetic fault codes and return non-conclusive checks."""

    try:
        query = DiagnosticQuery(
            fault_codes=fault_codes,
            symptoms=symptoms or [],
        )
    except ValidationError as exc:
        return ToolResponse(
            status="invalid_request",
            message="The diagnostic request is invalid.",
            errors=[
                ToolError(
                    code="VALIDATION_ERROR",
                    message=error["msg"],
                    details={"field": ".".join(map(str, error["loc"]))},
                )
                for error in exc.errors()
            ],
        ).model_dump(mode="json")

    results: list[dict[str, Any]] = []
    for code in query.fault_codes:
        rule = SYNTHETIC_RULES.get(code)
        if rule:
            results.append({"fault_code": code, "recognized": True, **rule})
        else:
            results.append(
                {
                    "fault_code": code,
                    "recognized": False,
                    "summary": "Code absent from the synthetic demonstration dataset.",
                    "checks": [],
                    "confidence": "unknown",
                }
            )

    return ToolResponse(
        status="success",
        message=f"Processed {len(results)} synthetic fault code(s).",
        data={
            "results": results,
            "reported_symptoms": query.symptoms,
            "diagnostic_status": "non_conclusive",
        },
    ).model_dump(mode="json")
