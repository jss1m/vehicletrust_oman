import pytest

from vehicletrust.extensions import db
from vehicletrust.models import Credential, Owner, PlateEntitlement, Vehicle
from vehicletrust.services import (
    ControlledSecurityError,
    physical_plate_for_credential,
    reactivate_and_bind_reserved_plate,
    reserve_physical_plate,
    transfer_plate_number,
)


def test_plate_number_transfer_without_active_entitlement_is_denied(ctx):
    credential = Credential.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    plate = physical_plate_for_credential(credential)
    entitlement = PlateEntitlement.query.filter_by(
        plate_number_id=plate.plate_number_id, status="ACTIVE"
    ).one()
    entitlement.status = "TRANSFER_PENDING"
    db.session.commit()
    buyer = Owner.query.filter_by(owner_reference="OWN-DEMO-B").one()
    vehicle = Vehicle.query.filter_by(vehicle_trust_id="VT-C3D8E2").one()
    with pytest.raises(ControlledSecurityError, match="entitlement"):
        transfer_plate_number(
            credential, buyer, vehicle, transaction_reference="RED-TEAM-NO-ENTITLEMENT"
        )


def test_reserved_plate_requires_explicit_controlled_restore(ctx):
    credential = Credential.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    vehicle = Vehicle.query.filter_by(vehicle_trust_id="VT-C3D8E2").one()
    reserve_physical_plate(
        credential, reason="Red-team reserve", transaction_reference="RED-TEAM-RESERVE"
    )
    reactivate_and_bind_reserved_plate(
        credential, vehicle, transaction_reference="CONTROLLED-RESTORE"
    )
    with pytest.raises(ControlledSecurityError, match="not reserved"):
        reactivate_and_bind_reserved_plate(
            credential, vehicle, transaction_reference="ILLEGAL-SECOND-RESTORE"
        )
