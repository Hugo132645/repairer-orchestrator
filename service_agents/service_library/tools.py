from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from common.schemas import RepairProcedureQuery, ToolError, ToolResponse
from common.tooling import observed_tool

SERVICE_NAME = "service_library_agent"
DATA_FILE = Path(__file__).resolve().parent / "data" / "repair_procedures.json"


def _load_procedures() -> list[dict[str, Any]]:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError("Procedure data must be a JSON list.")
    return payload


@observed_tool(SERVICE_NAME, "search_repair_procedures")
def search_repair_procedures(
    vehicle_model: str,
    fault_codes: list[str],
    market: str = "EU",
) -> dict[str, Any]:
    """Search synthetic repair procedures."""

    try:
        query = RepairProcedureQuery(
            vehicle_model=vehicle_model,
            fault_codes=fault_codes,
            market=market,
        )
    except ValidationError as exc:
        return ToolResponse(
            status="invalid_request",
            message="The repair-procedure request is invalid.",
            errors=[
                ToolError(
                    code="VALIDATION_ERROR",
                    message=error["msg"],
                    details={"field": ".".join(map(str, error["loc"]))},
                )
                for error in exc.errors()
            ],
        ).model_dump(mode="json")

    requested_codes = set(query.fault_codes)
    matches = [
        procedure
        for procedure in _load_procedures()
        if procedure["vehicle_model"].casefold() == query.vehicle_model.casefold()
        and procedure["market"].casefold() == query.market.casefold()
        and requested_codes.intersection({code.upper() for code in procedure["fault_codes"]})
    ]

    status = "success" if matches else "no_match"
    return ToolResponse(
        status=status,
        message=(
            f"Found {len(matches)} synthetic procedure(s)."
            if matches
            else "No synthetic procedure matched the supplied criteria."
        ),
        data={
            "match_count": len(matches),
            "procedures": matches,
            "source": "local_synthetic_json",
        },
    ).model_dump(mode="json")
