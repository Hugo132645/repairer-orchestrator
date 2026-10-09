from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from common.schemas import PartsQuery, ToolError, ToolResponse
from common.tooling import observed_tool

SERVICE_NAME = "parts_agent"

SYNTHETIC_PARTS: list[dict[str, Any]] = [
    {
        "part_number": "SYN-EU-COIL-001",
        "name": "Synthetic ignition coil",
        "vehicle_model": "Demo Compact Hatchback",
        "market": "EU",
        "availability": "in_stock",
        "quantity": 4,
        "estimated_delivery_days": 0,
    },
    {
        "part_number": "SYN-EU-CAT-001",
        "name": "Synthetic catalytic converter",
        "vehicle_model": "Demo Light Commercial Van",
        "market": "EU",
        "availability": "backorder",
        "quantity": 0,
        "estimated_delivery_days": 12,
    },
]


@observed_tool(SERVICE_NAME, "search_parts")
def search_parts(
    vehicle_model: str,
    part_name: str,
    market: str = "EU",
) -> dict[str, Any]:
    """Search a synthetic local parts catalogue."""

    try:
        query = PartsQuery(
            vehicle_model=vehicle_model,
            part_name=part_name,
            market=market,
        )
    except ValidationError as exc:
        return ToolResponse(
            status="invalid_request",
            message="The parts request is invalid.",
            errors=[
                ToolError(
                    code="VALIDATION_ERROR",
                    message=error["msg"],
                    details={"field": ".".join(map(str, error["loc"]))},
                )
                for error in exc.errors()
            ],
        ).model_dump(mode="json")

    matches = [
        part
        for part in SYNTHETIC_PARTS
        if part["vehicle_model"].casefold() == query.vehicle_model.casefold()
        and part["market"].casefold() == query.market.casefold()
        and query.part_name.casefold() in part["name"].casefold()
    ]

    status = "success" if matches else "no_match"
    return ToolResponse(
        status=status,
        message=(
            f"Found {len(matches)} synthetic part(s)."
            if matches
            else "No synthetic part matched the supplied criteria."
        ),
        data={
            "match_count": len(matches),
            "parts": matches,
            "source": "local_synthetic_catalogue",
        },
    ).model_dump(mode="json")
