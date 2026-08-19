from vehicletrust.services import run_scenario


def test_genuine_physical_plate_swap_has_specific_decision(ctx):
    result = run_scenario("swap")
    assert result["actual"] == "GENUINE_PLATE_WRONG_VEHICLE"
    assert result["details"]["steps"][1]["status"] == "PASS"
    assert result["details"]["steps"][5] == {
        "label": "Vehicle Proof",
        "status": "PASS",
    }
    assert "authentic" in result["details"]["reason"]
