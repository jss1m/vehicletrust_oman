from vehicletrust.models import AuditEvent
from vehicletrust.services import run_full_demo


def test_full_demo_passes_and_all_scenarios_leave_evidence(ctx):
    demo = run_full_demo()
    assert demo["passed"]
    assert demo["count"] == 21
    results = {item["actual"] for item in demo["results"]}
    assert {
        "VERIFIED",
        "VEHICLE_IDENTITY_MISMATCH",
        "GENUINE_PLATE_WRONG_VEHICLE",
        "INVALID_DIGITAL_SIGNATURE",
        "INVALID_VEHICLE_PROOF",
        "REPLAY_DETECTED",
        "EXPIRED_CHALLENGE",
        "CREDENTIAL_REVOKED",
        "SECURE_MODULE_UNAVAILABLE",
        "VERIFIED_IDENTITY_STOLEN_VEHICLE",
    }.issubset(results)
    events = AuditEvent.query.all()
    assert all(
        event.event_id and event.timestamp and event.result and event.risk_level for event in events
    )
