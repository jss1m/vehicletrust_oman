from vehicletrust.models import Credential, RebindingHistory
from vehicletrust.services import credential_content, run_scenario, verify_vehicle


def test_authorized_rebinding_preserves_history_and_changes_binding(ctx):
    result = run_scenario("rebinding")
    assert result["actual"] == "VERIFIED"
    history = RebindingHistory.query.one()
    old = Credential.query.filter_by(credential_id=history.old_credential_id).one()
    new = Credential.query.filter_by(credential_id=history.new_credential_id).one()
    assert old.status == "ACTIVE"
    assert old.plate_serial == new.plate_serial
    assert credential_content(old) == credential_content(new)
    assert (
        verify_vehicle(credential_content(new), "VT-7A82F1")["result"]
        == "VEHICLE_IDENTITY_MISMATCH"
    )
    assert verify_vehicle(credential_content(new), "VT-91B4D7")["result"] == "VERIFIED"
