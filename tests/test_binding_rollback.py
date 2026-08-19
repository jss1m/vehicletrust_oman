import pytest

from vehicletrust.extensions import db
from vehicletrust.models import Credential, PhysicalPlate, PlateVehicleBinding, Vehicle
from vehicletrust.services import authorized_rebind


def test_rebinding_rolls_back_all_changes_on_failure(ctx, monkeypatch):
    credential = Credential.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    vehicle = Vehicle.query.filter_by(vehicle_trust_id="VT-91B4D7").one()
    plate = PhysicalPlate.query.filter_by(credential_id=credential.credential_id).one()
    original_flush = db.session.flush

    def fail_flush(*args, **kwargs):
        raise RuntimeError("injected transaction failure")

    monkeypatch.setattr(db.session, "flush", fail_flush)
    with pytest.raises(RuntimeError, match="injected"):
        authorized_rebind(
            credential,
            vehicle,
            reason="Rollback test",
            authorization_reference="ROLLBACK-TEST",
        )
    monkeypatch.setattr(db.session, "flush", original_flush)
    db.session.expire_all()
    assert (
        PlateVehicleBinding.query.filter_by(physical_plate_id=plate.id, status="ACTIVE").count()
        == 1
    )
