from vehicletrust.services import run_scenario


def test_exact_qr_clone_is_authentic_but_wrong_vehicle(ctx):
    result = run_scenario("clone")
    assert result["actual"] == "VEHICLE_IDENTITY_MISMATCH"
    assert result["details"]["expected_vehicle"] == "VT-7A82F1"
    assert result["details"]["responding_vehicle"] == "VT-91B4D7"
    assert result["details"]["steps"][2] == {
        "label": "Issuer Signature",
        "status": "PASS",
    }
    assert result["details"]["steps"][-2]["status"] == "FAIL"
