from vehicletrust.credential_code import decode_and_verify_code
from vehicletrust.models import Credential, PhysicalPlate, PlateVehicleBinding
from vehicletrust.services import credential_content, issuer, run_lifecycle_scenario


def test_plate_uid_and_secure_code_stay_static_on_rebind(ctx):
    before = Credential.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    uid, code = before.plate_serial, credential_content(before)
    compact = decode_and_verify_code(code, issuer())
    assert "vehicle_trust_id" not in compact
    assert compact["plate_serial"] == uid
    assert run_lifecycle_scenario("keep_plate", reset=False)["passed"]
    assert Credential.query.filter_by(credential_id=before.credential_id).one().plate_serial == uid
    assert credential_content(before) == code
    plate = PhysicalPlate.query.filter_by(plate_uid=uid).one()
    assert PlateVehicleBinding.query.filter_by(physical_plate_id=plate.id).count() == 2
