from vehicletrust.models import AuditEvent, Challenge
from vehicletrust.services import run_scenario


def test_one_field_tamper_stops_before_challenge(ctx):
    result = run_scenario("tamper")
    assert result["actual"] == "INVALID_DIGITAL_SIGNATURE"
    assert Challenge.query.count() == 0
    event = AuditEvent.query.filter_by(event_id=result["details"]["event_id"]).one()
    assert event.failure_stage == "issuer_signature"
