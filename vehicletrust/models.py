from datetime import UTC, datetime

from .extensions import db


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_trust_id = db.Column(db.String(24), unique=True, nullable=False, index=True)
    full_vin = db.Column(db.String(32), unique=True, nullable=False)
    make = db.Column(db.String(40), nullable=False)
    model = db.Column(db.String(40), nullable=False)
    color = db.Column(db.String(24), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    vehicle_type = db.Column(db.String(30), nullable=False, default="Private SUV")
    original_plate_number = db.Column(db.String(12), nullable=False)
    original_plate_code = db.Column(db.String(4), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    registration_status = db.Column(db.String(20), nullable=False, default="REGISTERED")
    public_key_pem = db.Column(db.Text, nullable=True)
    public_key_fingerprint = db.Column(db.String(64), nullable=True)
    secure_key_ref = db.Column(db.String(160), nullable=True, unique=True)
    secure_module_status = db.Column(db.String(20), nullable=False, default="ONLINE")
    theft_status = db.Column(db.String(24), nullable=False, default="CLEAR")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    @property
    def masked_vin(self) -> str:
        return f"{self.full_vin[:3]}••••••••••{self.full_vin[-4:]}"


class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.String(48), unique=True, nullable=False, index=True)
    plate_serial = db.Column(db.String(48), unique=True, nullable=False, index=True)
    plate_number = db.Column(db.String(12), nullable=False)
    plate_code = db.Column(db.String(4), nullable=False)
    vehicle_trust_id = db.Column(
        db.String(24), db.ForeignKey("vehicle.vehicle_trust_id"), nullable=False
    )
    issuer = db.Column(db.String(100), nullable=False)
    issued_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    payload_json = db.Column(db.Text, nullable=False)
    signature_b64 = db.Column(db.Text, nullable=False)
    qr_filename = db.Column(db.String(160), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    revoked_at = db.Column(db.DateTime)
    superseded_by_id = db.Column(db.String(48))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class PlateBinding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(12), nullable=False, index=True)
    plate_code = db.Column(db.String(4), nullable=False)
    vehicle_trust_id = db.Column(
        db.String(24), db.ForeignKey("vehicle.vehicle_trust_id"), nullable=False
    )
    credential_id = db.Column(
        db.String(48), db.ForeignKey("credential.credential_id"), nullable=False
    )
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    effective_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    ended_at = db.Column(db.DateTime)
    reason = db.Column(db.String(200))
    authorization_reference = db.Column(db.String(80))
    operator = db.Column(db.String(80), default="Demo Admin")

    __table_args__ = (
        db.Index(
            "uq_active_plate_binding",
            "plate_number",
            "plate_code",
            unique=True,
            sqlite_where=db.text("status = 'ACTIVE'"),
        ),
    )


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.String(48), unique=True, nullable=False, index=True)
    credential_id = db.Column(db.String(48), nullable=False)
    expected_vehicle_id = db.Column(db.String(24), nullable=False)
    nonce_b64 = db.Column(db.String(128), nullable=False)
    payload_json = db.Column(db.Text, nullable=False)
    issued_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    responding_vehicle_id = db.Column(db.String(24))
    vehicle_signature_b64 = db.Column(db.Text)


class AuditEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(48), unique=True, nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow)
    event_type = db.Column(db.String(50), nullable=False)
    plate = db.Column(db.String(24))
    credential_id = db.Column(db.String(48))
    expected_vehicle = db.Column(db.String(24))
    responding_vehicle = db.Column(db.String(24))
    challenge_id = db.Column(db.String(48))
    result = db.Column(db.String(60), nullable=False)
    reason = db.Column(db.String(240))
    risk_level = db.Column(db.String(20), nullable=False)
    failure_stage = db.Column(db.String(50))
    actor = db.Column(db.String(80))
    plate_uid = db.Column(db.String(32))
    previous_vehicle = db.Column(db.String(24))
    new_vehicle = db.Column(db.String(24))
    previous_owner = db.Column(db.String(32))
    new_owner = db.Column(db.String(32))
    transaction_id = db.Column(db.String(80))
    timeline_json = db.Column(db.Text, nullable=False, default="[]")


class RebindingHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(48), unique=True, nullable=False)
    plate = db.Column(db.String(24), nullable=False)
    old_vehicle_id = db.Column(db.String(24), nullable=False)
    new_vehicle_id = db.Column(db.String(24), nullable=False)
    old_credential_id = db.Column(db.String(48), nullable=False)
    new_credential_id = db.Column(db.String(48), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    authorization_reference = db.Column(db.String(80), nullable=False)
    operator = db.Column(db.String(80), nullable=False)
    effective_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class Owner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_reference = db.Column(db.String(32), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class PlateNumber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(12), nullable=False)
    plate_code = db.Column(db.String(4), nullable=False)
    status = db.Column(db.String(24), nullable=False, default="ACTIVE")

    __table_args__ = (db.UniqueConstraint("plate_number", "plate_code"),)


class PhysicalPlate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_uid = db.Column(db.String(32), unique=True, nullable=False, index=True)
    plate_number_id = db.Column(db.Integer, db.ForeignKey("plate_number.id"), nullable=False)
    credential_id = db.Column(
        db.String(48), db.ForeignKey("credential.credential_id"), unique=True, nullable=False
    )
    issuer_id = db.Column(db.String(24), nullable=False, default="VTO1")
    issued_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    status = db.Column(db.String(24), nullable=False, default="ACTIVE")
    physical_status = db.Column(db.String(24), nullable=False, default="IN_SERVICE")
    replaced_by_id = db.Column(db.Integer, db.ForeignKey("physical_plate.id"))


class PlateEntitlement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("owner.id"), nullable=False)
    plate_number_id = db.Column(db.Integer, db.ForeignKey("plate_number.id"), nullable=False)
    valid_from = db.Column(db.DateTime, nullable=False, default=utcnow)
    valid_until = db.Column(db.DateTime)
    status = db.Column(db.String(24), nullable=False, default="ACTIVE")

    __table_args__ = (
        db.Index(
            "uq_active_plate_entitlement",
            "plate_number_id",
            unique=True,
            sqlite_where=db.text("status = 'ACTIVE'"),
        ),
    )


class VehicleOwnership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("owner.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=False)
    valid_from = db.Column(db.DateTime, nullable=False, default=utcnow)
    valid_until = db.Column(db.DateTime)
    status = db.Column(db.String(24), nullable=False, default="ACTIVE")

    __table_args__ = (
        db.Index(
            "uq_active_vehicle_ownership",
            "vehicle_id",
            unique=True,
            sqlite_where=db.text("status = 'ACTIVE'"),
        ),
    )


class PlateVehicleBinding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    physical_plate_id = db.Column(
        db.Integer, db.ForeignKey("physical_plate.id"), nullable=False, index=True
    )
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=False)
    valid_from = db.Column(db.DateTime, nullable=False, default=utcnow)
    valid_until = db.Column(db.DateTime)
    status = db.Column(db.String(24), nullable=False, default="ACTIVE")
    reason = db.Column(db.String(200))
    transaction_reference = db.Column(db.String(80), nullable=False)
    created_by = db.Column(db.String(80), nullable=False, default="Demo Admin")
    superseded_by = db.Column(db.Integer, db.ForeignKey("plate_vehicle_binding.id"))

    __table_args__ = (
        db.Index(
            "uq_active_physical_plate_binding",
            "physical_plate_id",
            unique=True,
            sqlite_where=db.text("status = 'ACTIVE'"),
        ),
    )
