from vehicletrust.models import AuditEvent
from vehicletrust.services import run_scenario


def test_normal_end_to_end_verification_and_audit(ctx):
    result = run_scenario("normal")
    assert result["actual"] == "VERIFIED"
    details = result["details"]
    assert details["expected_vehicle"] == "VT-7A82F1"
    assert details["responding_vehicle"] == "VT-7A82F1"
    assert details["challenge_id"]
    assert all(step["status"] == "PASS" for step in details["steps"])
    assert AuditEvent.query.filter_by(event_id=details["event_id"], result="VERIFIED").one()
