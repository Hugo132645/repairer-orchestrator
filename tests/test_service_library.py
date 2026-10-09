from service_agents.service_library.tools import search_repair_procedures


def test_exact_procedure_match() -> None:
    result = search_repair_procedures("Demo Compact Hatchback", ["P0301"], "EU")
    assert result["status"] == "success"
    assert result["data"]["match_count"] == 1


def test_unknown_procedure() -> None:
    result = search_repair_procedures("Demo Compact Hatchback", ["P9999"], "EU")
    assert result["status"] == "no_match"
