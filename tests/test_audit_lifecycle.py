from vehicletrust.models import AuditEvent
from vehicletrust.services import run_lifecycle_scenario


def test_lifecycle_operations_create_structured_audit_evidence(ctx):
    assert run_lifecycle_scenario("sell_plate_number")["passed"]
    types = {event.event_type for event in AuditEvent.query.all()}
    assert "PLATE_NUMBER_TRANSFERRED" in types
    assert "CREDENTIAL_ISSUED" in types
    assert all(
        event.event_id and event.timestamp and event.result for event in AuditEvent.query.all()
    )
    transfer = AuditEvent.query.filter_by(event_type="PLATE_NUMBER_TRANSFERRED").one()
    assert transfer.actor and transfer.plate_uid and transfer.transaction_id
    assert transfer.previous_owner and transfer.new_owner and transfer.new_vehicle
