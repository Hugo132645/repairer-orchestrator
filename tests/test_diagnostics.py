from service_agents.diagnostics.tools import interpret_fault_codes


def test_known_diagnostic_code() -> None:
    result = interpret_fault_codes(["p0301"], ["rough idle"])
    assert result["status"] == "success"
    assert result["data"]["results"][0]["recognized"] is True
    assert result["data"]["results"][0]["fault_code"] == "P0301"


def test_unknown_diagnostic_code_is_not_invented() -> None:
    result = interpret_fault_codes(["P9999"])
    assert result["status"] == "success"
    assert result["data"]["results"][0]["recognized"] is False
    assert result["data"]["results"][0]["checks"] == []
