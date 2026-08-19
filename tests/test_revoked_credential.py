from vehicletrust.services import run_scenario


def test_valid_signature_but_revoked_status_denied(ctx):
    result = run_scenario("revocation")
    assert result["actual"] == "CREDENTIAL_REVOKED"
    assert result["details"]["steps"][1]["status"] == "PASS"
    assert "operational status" in result["details"]["reason"]
