from vehicletrust.credential_code import tamper_code_field
from vehicletrust.extensions import db
from vehicletrust.models import RebindingHistory, Vehicle
from vehicletrust.services import (
    active_credential,
    credential_content,
    run_scenario,
    verify_vehicle,
)


def test_invalid_signature_never_verified(ctx):
    code = credential_content(active_credential("VT-7A82F1"))
    tampered = tamper_code_field(code, 1, 2)
    assert verify_vehicle(tampered, "VT-7A82F1")["result"] == "INVALID_DIGITAL_SIGNATURE"


def test_all_primary_security_invariants(ctx):
    expected = {
        "normal": "VERIFIED",
        "swap": "GENUINE_PLATE_WRONG_VEHICLE",
        "clone": "VEHICLE_IDENTITY_MISMATCH",
        "tamper": "INVALID_DIGITAL_SIGNATURE",
        "impersonation": "INVALID_VEHICLE_PROOF",
        "replay": "REPLAY_DETECTED",
        "expiry": "EXPIRED_CHALLENGE",
        "offline": "SECURE_MODULE_UNAVAILABLE",
        "revocation": "CREDENTIAL_REVOKED",
    }
    for scenario, decision in expected.items():
        assert run_scenario(scenario)["actual"] == decision


def test_failed_registry_dependency_cannot_verify(ctx):
    credential = active_credential("VT-7A82F1")
    code = credential_content(credential)
    vehicle = Vehicle.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    vehicle.public_key_pem = None
    db.session.commit()
    assert verify_vehicle(code, vehicle.vehicle_trust_id)["result"] != "VERIFIED"


def test_rebinding_preserves_evidence(ctx):
    assert run_scenario("rebinding")["actual"] == "VERIFIED"
    history = RebindingHistory.query.one()
    assert history.old_credential_id
    assert history.new_credential_id
    assert history.old_credential_id == history.new_credential_id
