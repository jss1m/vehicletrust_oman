from vehicletrust.models import AuditEvent, Challenge
from vehicletrust.services import (
    active_credential,
    create_challenge,
    credential_content,
    run_scenario,
    submit_challenge_response,
    verify_vehicle,
)


def test_consumed_challenge_rejected_and_separately_audited(ctx):
    result = run_scenario("replay")
    assert result["actual"] == "REPLAY_DETECTED"
    challenge = Challenge.query.filter_by(challenge_id=result["details"]["challenge_id"]).one()
    assert challenge.used_at is not None
    assert (
        AuditEvent.query.filter_by(challenge_id=challenge.challenge_id, result="VERIFIED").count()
        == 1
    )
    assert (
        AuditEvent.query.filter_by(
            challenge_id=challenge.challenge_id, result="REPLAY_DETECTED"
        ).count()
        == 1
    )


def test_old_response_fails_for_new_nonce(ctx):
    credential = active_credential("VT-7A82F1")
    first = verify_vehicle(credential_content(credential), "VT-7A82F1")
    old = Challenge.query.filter_by(challenge_id=first["challenge_id"]).one()
    payload = __import__("json").loads(credential.payload_json)
    new = create_challenge(payload)
    result = submit_challenge_response(new, "VT-7A82F1", old.vehicle_signature_b64)
    assert result["result"] == "INVALID_VEHICLE_PROOF"
