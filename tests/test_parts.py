from service_agents.parts.tools import search_parts


def test_parts_match() -> None:
    result = search_parts("Demo Compact Hatchback", "ignition coil", "EU")
    assert result["status"] == "success"
    assert result["data"]["match_count"] == 1
    assert result["data"]["parts"][0]["availability"] == "in_stock"


def test_parts_no_match() -> None:
    result = search_parts("Demo Compact Hatchback", "catalytic converter", "EU")
    assert result["status"] == "no_match"
    assert result["data"]["parts"] == []
