import base64
import json
import re
import secrets
import threading
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import qrcode
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from flask import current_app
from sqlalchemy.exc import IntegrityError

from .credential_code import (
    CompactCredentialError,
    CompactSignatureError,
    binary_code_from_credential,
    code_from_credential,
    create_signed_code,
    decode_and_verify_code,
    tamper_code_field,
)
from .crypto import ISSUER_NAME, DemoIssuerAuthority, canonical_json, fingerprint
from .extensions import db
from .models import (
    AuditEvent,
    Challenge,
    Credential,
    Owner,
    PhysicalPlate,
    PlateBinding,
    PlateEntitlement,
    PlateNumber,
    PlateVehicleBinding,
    RebindingHistory,
    Vehicle,
    VehicleOwnership,
    utcnow,
)
from .secure_module import SimulatedVehicleSecureModule


class ControlledSecurityError(ValueError):
    pass


_lifecycle_lock = threading.RLock()


def iso(value: datetime) -> str:
    return value.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")


def issuer() -> DemoIssuerAuthority:
    return DemoIssuerAuthority(current_app.instance_path)


def credential_content(credential: Credential) -> str:
    return code_from_credential(credential)


def render_credential_qr(credential: Credential) -> None:
    qr_dir = Path(current_app.static_folder) / "generated_qr"
    qr_dir.mkdir(parents=True, exist_ok=True)
    qr = qrcode.QRCode(
        version=None,
        box_size=5,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        mask_pattern=4,
    )
    qr.add_data(binary_code_from_credential(credential))
    qr.make(fit=True)
    qr.make_image(fill_color="#111827", back_color="white").save(qr_dir / credential.qr_filename)


def audit(
    *,
    event_type: str,
    result: str,
    risk: str,
    plate: str | None = None,
    credential_id: str | None = None,
    expected: str | None = None,
    responding: str | None = None,
    challenge_id: str | None = None,
    reason: str | None = None,
    failure_stage: str | None = None,
    timeline: list[str] | None = None,
    actor: str | None = None,
    plate_uid: str | None = None,
    previous_vehicle: str | None = None,
    new_vehicle: str | None = None,
    previous_owner: str | None = None,
    new_owner: str | None = None,
    transaction_id: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_id=f"EVT-{uuid.uuid4().hex[:12].upper()}",
        event_type=event_type,
        plate=plate,
        credential_id=credential_id,
        expected_vehicle=expected,
        responding_vehicle=responding,
        challenge_id=challenge_id,
        result=result,
        reason=reason,
        risk_level=risk,
        failure_stage=failure_stage,
        actor=actor,
        plate_uid=plate_uid,
        previous_vehicle=previous_vehicle,
        new_vehicle=new_vehicle,
        previous_owner=previous_owner,
        new_owner=new_owner,
        transaction_id=transaction_id,
        timeline_json=json.dumps(timeline or []),
    )
    db.session.add(event)
    db.session.commit()
    return event


def provision_vehicle(data: dict) -> Vehicle:
    key_ref, public_pem = SimulatedVehicleSecureModule.provision(
        current_app.instance_path, data["vehicle_trust_id"]
    )
    vehicle = Vehicle(
        **data,
        public_key_pem=public_pem,
        public_key_fingerprint=fingerprint(public_pem),
        secure_key_ref=key_ref,
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle


def issue_credential(
    vehicle: Vehicle,
    *,
    plate_number: str | None = None,
    plate_code: str | None = None,
    years: int = 1,
    reason: str = "Initial demo issuance",
    authorization_reference: str = "DEMO-ISSUE",
) -> Credential:
    plate_number = plate_number or vehicle.original_plate_number
    plate_code = plate_code or vehicle.original_plate_code
    if not re.fullmatch(r"\d{4,6}", plate_number) or not re.fullmatch(r"[A-Z]{1,3}", plate_code):
        raise ControlledSecurityError("Invalid prototype plate format")
    now = utcnow()
    payload = {
        "plate_number": plate_number,
        "plate_code": plate_code,
        "plate_serial": f"PLT-OM-{secrets.token_hex(6).upper()}",
        "vehicle_trust_id": vehicle.vehicle_trust_id,
        "credential_id": f"VTC-{uuid.uuid4().hex[:16].upper()}",
        "issuer": ISSUER_NAME,
        "issued_at": iso(now),
        "expires_at": iso(now + timedelta(days=365 * years)),
        "version": 1,
        "vehicle_public_key_fingerprint": vehicle.public_key_fingerprint,
    }
    _, signature = create_signed_code(payload, issuer())
    qr_name = f"{payload['credential_id']}.png"
    credential = Credential(
        credential_id=payload["credential_id"],
        plate_serial=payload["plate_serial"],
        plate_number=plate_number,
        plate_code=plate_code,
        vehicle_trust_id=vehicle.vehicle_trust_id,
        issuer=ISSUER_NAME,
        issued_at=now,
        expires_at=now + timedelta(days=365 * years),
        version=1,
        payload_json=canonical_json(payload).decode(),
        signature_b64=signature,
        qr_filename=qr_name,
    )
    db.session.add(credential)
    try:
        db.session.flush()
        binding = PlateBinding(
            plate_number=plate_number,
            plate_code=plate_code,
            vehicle_trust_id=vehicle.vehicle_trust_id,
            credential_id=credential.credential_id,
            reason=reason,
            authorization_reference=authorization_reference,
        )
        db.session.add(binding)
        plate_number_record = PlateNumber.query.filter_by(
            plate_number=plate_number, plate_code=plate_code
        ).first()
        if not plate_number_record:
            plate_number_record = PlateNumber(plate_number=plate_number, plate_code=plate_code)
            db.session.add(plate_number_record)
            db.session.flush()
        physical_plate = PhysicalPlate(
            plate_uid=payload["plate_serial"],
            plate_number_id=plate_number_record.id,
            credential_id=credential.credential_id,
            issuer_id="VTO1",
        )
        db.session.add(physical_plate)
        db.session.flush()
        lifecycle_binding = PlateVehicleBinding(
            physical_plate_id=physical_plate.id,
            vehicle_id=vehicle.id,
            reason=reason,
            transaction_reference=authorization_reference,
        )
        db.session.add(lifecycle_binding)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ControlledSecurityError(
            "Duplicate credential, serial, or active plate binding"
        ) from exc

    if current_app.config["GENERATE_QR_IMAGES"]:
        render_credential_qr(credential)
    audit(
        event_type="CREDENTIAL_ISSUED",
        result="CREDENTIAL_ISSUED",
        risk="INFO",
        plate=f"{plate_number} {plate_code}",
        credential_id=credential.credential_id,
        expected=vehicle.vehicle_trust_id,
        reason=reason,
        timeline=[
            "Vehicle selected",
            "Canonical payload created",
            "Issuer signature created",
            "QR generated",
        ],
        plate_uid=credential.plate_serial,
        actor="Demo Admin",
        transaction_id=authorization_reference,
    )
    return credential


def _decode_registry_credential(content: str) -> tuple[dict, Credential]:
    if not content or len(content.encode()) > current_app.config["MAX_CREDENTIAL_BYTES"]:
        raise ControlledSecurityError("Credential is empty or oversized")
    reference = decode_and_verify_code(content, issuer())
    credential = Credential.query.filter_by(credential_id=reference["credential_id"]).first()
    if not credential:
        raise ControlledSecurityError("Signed credential reference is not in the registry")
    if (
        reference["plate_serial"] != credential.plate_serial
        or reference["version"] != credential.version
    ):
        raise ControlledSecurityError("Credential reference does not match the registry")
    return json.loads(credential.payload_json), credential


def _decision(
    result: str,
    *,
    payload: dict | None,
    responding: str | None,
    challenge: Challenge | None = None,
    reason: str,
    stage: str | None = None,
    risk: str = "CRITICAL",
    event_type: str = "VEHICLE_VERIFICATION",
    steps: list[dict] | None = None,
) -> dict:
    event = audit(
        event_type=event_type,
        result=result,
        risk=risk,
        plate=(f"{payload['plate_number']} {payload['plate_code']}" if payload else None),
        credential_id=(payload.get("credential_id") if payload else None),
        expected=(payload.get("vehicle_trust_id") if payload else None),
        responding=responding,
        challenge_id=(challenge.challenge_id if challenge else None),
        reason=reason,
        failure_stage=stage,
        timeline=[step["label"] for step in steps or []],
    )
    return {
        "result": result,
        "reason": reason,
        "risk": risk,
        "event_id": event.event_id,
        "expected_vehicle": payload.get("vehicle_trust_id") if payload else None,
        "responding_vehicle": responding,
        "credential_id": payload.get("credential_id") if payload else None,
        "challenge_id": challenge.challenge_id if challenge else None,
        "steps": steps or [],
    }


def create_challenge(payload: dict, *, expired: bool = False) -> Challenge:
    now = utcnow()
    ttl = current_app.config["CHALLENGE_TTL_SECONDS"]
    expires_at = now - timedelta(seconds=1) if expired else now + timedelta(seconds=ttl)
    data = {
        "challenge_id": f"CH-{uuid.uuid4().hex.upper()}",
        "credential_id": payload["credential_id"],
        "expected_vehicle_id": payload["vehicle_trust_id"],
        "nonce": base64.b64encode(secrets.token_bytes(32)).decode(),
        "timestamp": iso(now),
        "expiry": iso(expires_at),
    }
    challenge = Challenge(
        challenge_id=data["challenge_id"],
        credential_id=data["credential_id"],
        expected_vehicle_id=data["expected_vehicle_id"],
        nonce_b64=data["nonce"],
        payload_json=canonical_json(data).decode(),
        issued_at=now,
        expires_at=expires_at,
    )
    db.session.add(challenge)
    db.session.commit()
    return challenge


def submit_challenge_response(
    challenge: Challenge,
    responding_vehicle_id: str,
    signature_b64: str,
    *,
    mismatch_result: str = "VEHICLE_IDENTITY_MISMATCH",
) -> dict:
    payload = json.loads(
        Credential.query.filter_by(credential_id=challenge.credential_id).first().payload_json
    )
    payload["vehicle_trust_id"] = challenge.expected_vehicle_id
    base_steps = [
        {"label": "Plate Read", "status": "PASS"},
        {"label": "Credential Decode", "status": "PASS"},
        {"label": "Issuer Signature", "status": "PASS"},
        {"label": "Registry Lookup", "status": "PASS"},
        {"label": "Challenge Issued", "status": "PASS"},
    ]
    if challenge.used_at:
        return _decision(
            "REPLAY_DETECTED",
            payload=payload,
            responding=responding_vehicle_id,
            challenge=challenge,
            reason="The one-time challenge was already consumed.",
            stage="replay_protection",
            steps=base_steps + [{"label": "Replay Protection", "status": "FAIL"}],
        )
    if utcnow() >= challenge.expires_at:
        return _decision(
            "EXPIRED_CHALLENGE",
            payload=payload,
            responding=responding_vehicle_id,
            challenge=challenge,
            reason="The challenge expired before the response was accepted.",
            stage="challenge_expiry",
            steps=base_steps + [{"label": "Challenge Freshness", "status": "FAIL"}],
        )
    responding = Vehicle.query.filter_by(vehicle_trust_id=responding_vehicle_id).first()
    if not responding:
        return _decision(
            "UNKNOWN_VEHICLE",
            payload=payload,
            responding=responding_vehicle_id,
            challenge=challenge,
            reason="The cryptographic identity is not registered.",
            stage="registry_lookup",
            steps=base_steps[:3] + [{"label": "Registry Lookup", "status": "FAIL"}],
        )
    try:
        if not responding.public_key_pem:
            raise ValueError("Missing vehicle public key")
        signature = base64.b64decode(signature_b64, validate=True)
        public_key = serialization.load_pem_public_key(responding.public_key_pem.encode())
        public_key.verify(signature, challenge.payload_json.encode(), ec.ECDSA(hashes.SHA256()))
    except (InvalidSignature, ValueError, TypeError):
        challenge.used_at = utcnow()
        db.session.commit()
        return _decision(
            "INVALID_VEHICLE_PROOF",
            payload=payload,
            responding=responding_vehicle_id,
            challenge=challenge,
            reason="Vehicle proof could not be verified. The decision failed closed.",
            stage="vehicle_hardware_proof",
            steps=base_steps + [{"label": "Vehicle Proof", "status": "FAIL"}],
        )
    challenge.used_at = utcnow()
    challenge.responding_vehicle_id = responding_vehicle_id
    challenge.vehicle_signature_b64 = signature_b64
    db.session.commit()
    proof_steps = base_steps + [{"label": "Vehicle Proof", "status": "PASS"}]
    if responding_vehicle_id != challenge.expected_vehicle_id:
        return _decision(
            mismatch_result,
            payload=payload,
            responding=responding_vehicle_id,
            challenge=challenge,
            reason=(
                "The plate credential is authentic, but the responding vehicle does not match "
                "the vehicle registered to this plate."
            ),
            stage="plate_vehicle_binding",
            steps=proof_steps
            + [
                {"label": "Plate ↔ Vehicle Binding", "status": "FAIL"},
                {"label": "Decision", "status": "FAIL"},
            ],
        )
    final_result = (
        "VERIFIED_IDENTITY_STOLEN_VEHICLE"
        if responding.theft_status == "REPORTED_STOLEN"
        else "VERIFIED"
    )
    return _decision(
        final_result,
        payload=payload,
        responding=responding_vehicle_id,
        challenge=challenge,
        reason=(
            "Identity is confirmed, but the registry reports the vehicle as stolen."
            if responding.theft_status == "REPORTED_STOLEN"
            else "Fresh vehicle proof matches the active physical-plate binding."
        ),
        risk="CRITICAL" if responding.theft_status == "REPORTED_STOLEN" else "INFO",
        steps=proof_steps
        + [
            {"label": "Plate ↔ Vehicle Binding", "status": "PASS"},
            {"label": "Decision", "status": "PASS"},
        ],
    )


def verify_vehicle(
    content: str,
    responding_vehicle_id: str,
    *,
    mismatch_result: str = "VEHICLE_IDENTITY_MISMATCH",
    expired_challenge: bool = False,
) -> dict:
    steps = [{"label": "Plate Read", "status": "PASS"}]
    try:
        payload, credential = _decode_registry_credential(content)
    except CompactSignatureError as exc:
        return _decision(
            "INVALID_DIGITAL_SIGNATURE",
            payload=None,
            responding=responding_vehicle_id,
            reason=str(exc),
            stage="issuer_signature",
            steps=steps
            + [
                {"label": "Credential Decode", "status": "PASS"},
                {"label": "Issuer Signature", "status": "FAIL"},
            ],
        )
    except CompactCredentialError as exc:
        return _decision(
            "TAMPERED_CREDENTIAL",
            payload=None,
            responding=responding_vehicle_id,
            reason=str(exc),
            stage="credential_decode",
            steps=steps + [{"label": "Credential Decode", "status": "FAIL"}],
        )
    except ControlledSecurityError as exc:
        return _decision(
            "TAMPERED_CREDENTIAL",
            payload=None,
            responding=responding_vehicle_id,
            reason=str(exc),
            stage="registry_lookup",
            steps=steps
            + [
                {"label": "Credential Decode", "status": "PASS"},
                {"label": "Issuer Signature", "status": "PASS"},
                {"label": "Registry Lookup", "status": "FAIL"},
            ],
        )
    steps.extend(
        [
            {"label": "Credential Decode", "status": "PASS"},
            {"label": "Issuer Signature", "status": "PASS"},
        ]
    )
    if credential.issuer != ISSUER_NAME:
        return _decision(
            "UNKNOWN_ISSUER",
            payload=payload,
            responding=responding_vehicle_id,
            reason="Credential issuer is not trusted.",
            stage="credential_signature",
            steps=steps + [{"label": "Registry Lookup", "status": "FAIL"}],
        )
    if credential.status in {"REVOKED", "SUPERSEDED"}:
        return _decision(
            "CREDENTIAL_REVOKED",
            payload=payload,
            responding=responding_vehicle_id,
            reason=f"Signature is valid, but operational status is {credential.status}.",
            stage="credential_status",
            steps=steps + [{"label": "Credential Status", "status": "FAIL"}],
        )
    if utcnow() >= credential.expires_at:
        return _decision(
            "EXPIRED_CREDENTIAL",
            payload=payload,
            responding=responding_vehicle_id,
            reason="Credential validity period has ended.",
            stage="credential_status",
            steps=steps + [{"label": "Credential Status", "status": "FAIL"}],
        )
    physical_plate = PhysicalPlate.query.filter_by(
        credential_id=credential.credential_id, plate_uid=credential.plate_serial
    ).first()
    if not physical_plate:
        return _decision(
            "REGISTRY_UNAVAILABLE",
            payload=payload,
            responding=responding_vehicle_id,
            reason="Physical plate identity is absent from the registry.",
            stage="registry_lookup",
            steps=steps + [{"label": "Registry Lookup", "status": "FAIL"}],
        )
    status_results = {
        "RETIRED": "RETIRED_PHYSICAL_PLATE",
        "LOST": "LOST_PLATE",
        "STOLEN": "STOLEN_PLATE",
        "REVOKED": "REVOKED_PLATE",
        "REPLACED": "REVOKED_PLATE",
        "RESERVED": "RESERVED_PLATE",
    }
    if physical_plate.status in status_results:
        return _decision(
            status_results[physical_plate.status],
            payload=payload,
            responding=responding_vehicle_id,
            reason=(
                "Signature is valid, but the physical plate registry status is "
                f"{physical_plate.status}."
            ),
            stage="plate_status",
            steps=steps + [{"label": "Registry Lookup", "status": "FAIL"}],
        )
    binding = PlateVehicleBinding.query.filter_by(
        physical_plate_id=physical_plate.id, status="ACTIVE"
    ).first()
    if not binding:
        return _decision(
            "RESERVED_PLATE",
            payload=payload,
            responding=responding_vehicle_id,
            reason="The physical plate has no active vehicle binding.",
            stage="plate_vehicle_binding",
            steps=steps + [{"label": "Registry Lookup", "status": "FAIL"}],
        )
    expected = db.session.get(Vehicle, binding.vehicle_id)
    if not expected:
        return _decision(
            "UNKNOWN_VEHICLE",
            payload=payload,
            responding=responding_vehicle_id,
            reason="Expected vehicle is not present in the registry.",
            stage="registry_lookup",
            steps=steps + [{"label": "Registry Lookup", "status": "FAIL"}],
        )
    payload["vehicle_trust_id"] = expected.vehicle_trust_id
    responding = Vehicle.query.filter_by(vehicle_trust_id=responding_vehicle_id).first()
    if not responding:
        return _decision(
            "UNKNOWN_VEHICLE",
            payload=payload,
            responding=responding_vehicle_id,
            reason="Responding vehicle is not present in the registry.",
            stage="registry_lookup",
            steps=steps + [{"label": "Registry Lookup", "status": "FAIL"}],
        )
    challenge = create_challenge(payload, expired=expired_challenge)
    module = SimulatedVehicleSecureModule(
        responding.secure_key_ref, responding.secure_module_status
    )
    try:
        response_signature = module.sign_challenge(challenge.payload_json.encode())
    except RuntimeError:
        return _decision(
            "SECURE_MODULE_UNAVAILABLE",
            payload=payload,
            responding=responding_vehicle_id,
            challenge=challenge,
            reason="Vehicle secure module is unavailable; identity was not asserted.",
            stage="vehicle_hardware_proof",
            steps=steps + [{"label": "Vehicle Proof", "status": "FAIL"}],
        )
    return submit_challenge_response(
        challenge, responding_vehicle_id, response_signature, mismatch_result=mismatch_result
    )


def revoke_credential(credential: Credential, reason: str = "Demo revocation") -> None:
    credential.status = "REVOKED"
    credential.revoked_at = utcnow()
    db.session.commit()
    audit(
        event_type="CREDENTIAL_REVOKED",
        result="CREDENTIAL_REVOKED",
        risk="WARNING",
        plate=f"{credential.plate_number} {credential.plate_code}",
        credential_id=credential.credential_id,
        expected=credential.vehicle_trust_id,
        reason=reason,
        timeline=["Revocation requested", "Credential status changed to REVOKED"],
    )


def authorized_rebind(
    old_credential: Credential,
    new_vehicle: Vehicle,
    *,
    reason: str,
    authorization_reference: str,
    operator: str = "Demo Admin",
) -> Credential:
    with _lifecycle_lock:
        physical_plate = PhysicalPlate.query.filter_by(
            credential_id=old_credential.credential_id
        ).first()
        if not physical_plate or physical_plate.status != "ACTIVE":
            raise ControlledSecurityError("Physical plate is not active")
        binding = PlateVehicleBinding.query.filter_by(
            physical_plate_id=physical_plate.id, status="ACTIVE"
        ).first()
        if not binding:
            raise ControlledSecurityError("No active binding exists for this physical plate")
        old_vehicle = db.session.get(Vehicle, binding.vehicle_id)
        if old_vehicle.vehicle_trust_id != old_credential.vehicle_trust_id:
            raise ControlledSecurityError("Binding changed; reload before retrying the transaction")
        plate_number = db.session.get(PlateNumber, physical_plate.plate_number_id)
        entitlement = PlateEntitlement.query.filter_by(
            plate_number_id=plate_number.id, status="ACTIVE"
        ).first()
        if not entitlement:
            raise ControlledSecurityError("No active plate-number entitlement")
        if new_vehicle.status != "ACTIVE" or new_vehicle.registration_status != "REGISTERED":
            raise ControlledSecurityError("Destination vehicle is not eligible")
        now = utcnow()
        try:
            destination_binding = PlateVehicleBinding.query.filter_by(
                vehicle_id=new_vehicle.id, status="ACTIVE"
            ).first()
            if destination_binding and destination_binding.physical_plate_id != physical_plate.id:
                destination_binding.status = "SUPERSEDED"
                destination_binding.valid_until = now
                destination_plate = db.session.get(
                    PhysicalPlate, destination_binding.physical_plate_id
                )
                destination_plate.status = "RESERVED"
                destination_credential = Credential.query.filter_by(
                    credential_id=destination_plate.credential_id
                ).first()
                destination_legacy = PlateBinding.query.filter_by(
                    credential_id=destination_credential.credential_id, status="ACTIVE"
                ).first()
                if destination_legacy:
                    destination_legacy.status = "SUPERSEDED"
                    destination_legacy.ended_at = now
            binding.status = "SUPERSEDED"
            binding.valid_until = now
            legacy = PlateBinding.query.filter_by(
                credential_id=old_credential.credential_id, status="ACTIVE"
            ).first()
            if legacy:
                legacy.status = "SUPERSEDED"
                legacy.ended_at = now
            new_binding = PlateVehicleBinding(
                physical_plate_id=physical_plate.id,
                vehicle_id=new_vehicle.id,
                reason=reason,
                transaction_reference=authorization_reference,
                created_by=operator,
            )
            db.session.add(new_binding)
            db.session.flush()
            binding.superseded_by = new_binding.id
            db.session.add(
                PlateBinding(
                    plate_number=plate_number.plate_number,
                    plate_code=plate_number.plate_code,
                    vehicle_trust_id=new_vehicle.vehicle_trust_id,
                    credential_id=old_credential.credential_id,
                    reason=reason,
                    authorization_reference=authorization_reference,
                    operator=operator,
                )
            )
            history = RebindingHistory(
                event_id=f"REB-{uuid.uuid4().hex[:12].upper()}",
                plate=f"{plate_number.plate_number} {plate_number.plate_code}",
                old_vehicle_id=old_vehicle.vehicle_trust_id,
                new_vehicle_id=new_vehicle.vehicle_trust_id,
                old_credential_id=old_credential.credential_id,
                new_credential_id=old_credential.credential_id,
                reason=reason,
                authorization_reference=authorization_reference,
                operator=operator,
            )
            db.session.add(history)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    audit(
        event_type="PLATE_REBOUND",
        result="REBINDING_COMPLETED",
        risk="INFO",
        plate=history.plate,
        credential_id=old_credential.credential_id,
        expected=new_vehicle.vehicle_trust_id,
        reason=f"{reason} ({authorization_reference})",
        timeline=[
            "Entitlement validated",
            "Old binding superseded",
            "New binding activated",
            "Static Plate UID and secure code preserved",
        ],
        actor=operator,
        plate_uid=physical_plate.plate_uid,
        previous_vehicle=old_vehicle.vehicle_trust_id,
        new_vehicle=new_vehicle.vehicle_trust_id,
        transaction_id=authorization_reference,
    )
    return old_credential


def owner_for_vehicle(vehicle: Vehicle) -> Owner | None:
    ownership = VehicleOwnership.query.filter_by(vehicle_id=vehicle.id, status="ACTIVE").first()
    return db.session.get(Owner, ownership.owner_id) if ownership else None


def physical_plate_for_credential(credential: Credential) -> PhysicalPlate:
    plate = PhysicalPlate.query.filter_by(credential_id=credential.credential_id).first()
    if not plate:
        raise ControlledSecurityError("Physical plate is not registered")
    return plate


def transfer_vehicle_ownership(
    vehicle: Vehicle,
    new_owner: Owner,
    *,
    transaction_reference: str,
    operator: str = "Demo Admin",
) -> VehicleOwnership:
    with _lifecycle_lock:
        current = VehicleOwnership.query.filter_by(vehicle_id=vehicle.id, status="ACTIVE").first()
        if not current:
            raise ControlledSecurityError("Vehicle has no active owner")
        if current.owner_id == new_owner.id:
            raise ControlledSecurityError("Vehicle already belongs to this owner")
        old_owner = db.session.get(Owner, current.owner_id)
        now = utcnow()
        current.status = "CLOSED"
        current.valid_until = now
        replacement = VehicleOwnership(owner_id=new_owner.id, vehicle_id=vehicle.id)
        db.session.add(replacement)
        db.session.commit()
    audit(
        event_type="OWNERSHIP_TRANSFERRED",
        result="OWNERSHIP_CHANGED_BINDING_REMAINS",
        risk="INFO",
        expected=vehicle.vehicle_trust_id,
        reason=(
            f"{old_owner.owner_reference} → {new_owner.owner_reference}; "
            f"transaction {transaction_reference}; operator {operator}"
        ),
        actor=operator,
        previous_owner=old_owner.owner_reference,
        new_owner=new_owner.owner_reference,
        transaction_id=transaction_reference,
    )
    return replacement


def reserve_physical_plate(
    credential: Credential,
    *,
    reason: str,
    transaction_reference: str,
) -> PhysicalPlate:
    with _lifecycle_lock:
        plate = physical_plate_for_credential(credential)
        binding = PlateVehicleBinding.query.filter_by(
            physical_plate_id=plate.id, status="ACTIVE"
        ).first()
        if not binding:
            raise ControlledSecurityError("Plate has no active binding")
        binding.status = "SUPERSEDED"
        binding.valid_until = utcnow()
        legacy = PlateBinding.query.filter_by(
            credential_id=credential.credential_id, status="ACTIVE"
        ).first()
        if legacy:
            legacy.status = "SUPERSEDED"
            legacy.ended_at = utcnow()
        plate.status = "RESERVED"
        db.session.commit()
    audit(
        event_type="PLATE_RESERVED",
        result="PLATE_RESERVED",
        risk="INFO",
        plate=f"{credential.plate_number} {credential.plate_code}",
        credential_id=credential.credential_id,
        reason=f"{reason} ({transaction_reference})",
        actor="Demo Admin",
        plate_uid=plate.plate_uid,
        transaction_id=transaction_reference,
    )
    return plate


def reactivate_and_bind_reserved_plate(
    credential: Credential,
    vehicle: Vehicle,
    *,
    transaction_reference: str,
) -> PhysicalPlate:
    with _lifecycle_lock:
        plate = physical_plate_for_credential(credential)
        if plate.status != "RESERVED":
            raise ControlledSecurityError("Plate is not reserved")
        if PlateVehicleBinding.query.filter_by(physical_plate_id=plate.id, status="ACTIVE").first():
            raise ControlledSecurityError("Plate already has an active binding")
        plate.status = "ACTIVE"
        db.session.add(
            PlateVehicleBinding(
                physical_plate_id=plate.id,
                vehicle_id=vehicle.id,
                reason="Reserved plate assigned to vehicle",
                transaction_reference=transaction_reference,
            )
        )
        db.session.commit()
    audit(
        event_type="PLATE_BOUND",
        result="PLATE_BOUND",
        risk="INFO",
        credential_id=credential.credential_id,
        expected=vehicle.vehicle_trust_id,
        reason=transaction_reference,
        actor="Demo Admin",
        plate_uid=plate.plate_uid,
        new_vehicle=vehicle.vehicle_trust_id,
        transaction_id=transaction_reference,
    )
    return plate


def transfer_plate_number(
    credential: Credential,
    buyer: Owner,
    buyer_vehicle: Vehicle,
    *,
    transaction_reference: str,
) -> Credential:
    with _lifecycle_lock:
        old_plate = physical_plate_for_credential(credential)
        number = db.session.get(PlateNumber, old_plate.plate_number_id)
        entitlement = PlateEntitlement.query.filter_by(
            plate_number_id=number.id, status="ACTIVE"
        ).first()
        if not entitlement:
            raise ControlledSecurityError("Seller has no active entitlement")
        buyer_ownership = VehicleOwnership.query.filter_by(
            owner_id=buyer.id, vehicle_id=buyer_vehicle.id, status="ACTIVE"
        ).first()
        if not buyer_ownership:
            raise ControlledSecurityError("Buyer does not own the destination vehicle")
        now = utcnow()
        current_binding = PlateVehicleBinding.query.filter_by(
            physical_plate_id=old_plate.id, status="ACTIVE"
        ).first()
        if current_binding:
            current_binding.status = "SUPERSEDED"
            current_binding.valid_until = now
        legacy = PlateBinding.query.filter_by(
            credential_id=credential.credential_id, status="ACTIVE"
        ).first()
        if legacy:
            legacy.status = "SUPERSEDED"
            legacy.ended_at = now
        entitlement.status = "CLOSED"
        entitlement.valid_until = now
        old_plate.status = "RETIRED"
        db.session.add(PlateEntitlement(owner_id=buyer.id, plate_number_id=number.id))
        db.session.commit()
    new_credential = issue_credential(
        buyer_vehicle,
        plate_number=number.plate_number,
        plate_code=number.plate_code,
        reason="Plate-number ownership transfer and physical reissue",
        authorization_reference=transaction_reference,
    )
    audit(
        event_type="PLATE_NUMBER_TRANSFERRED",
        result="OLD_PLATE_RETIRED_NEW_PLATE_ISSUED",
        risk="INFO",
        plate=f"{number.plate_number} {number.plate_code}",
        credential_id=new_credential.credential_id,
        expected=buyer_vehicle.vehicle_trust_id,
        reason=transaction_reference,
        actor="Demo Admin",
        plate_uid=old_plate.plate_uid,
        previous_owner=db.session.get(Owner, entitlement.owner_id).owner_reference,
        new_owner=buyer.owner_reference,
        new_vehicle=buyer_vehicle.vehicle_trust_id,
        transaction_id=transaction_reference,
    )
    return new_credential


def reissue_physical_plate(
    credential: Credential,
    *,
    old_status: str,
    reason: str,
    transaction_reference: str,
) -> Credential:
    if old_status not in {"LOST", "STOLEN", "REPLACED"}:
        raise ControlledSecurityError("Unsupported reissue status")
    with _lifecycle_lock:
        old_plate = physical_plate_for_credential(credential)
        binding = PlateVehicleBinding.query.filter_by(
            physical_plate_id=old_plate.id, status="ACTIVE"
        ).first()
        if not binding:
            raise ControlledSecurityError("Plate has no active binding")
        vehicle = db.session.get(Vehicle, binding.vehicle_id)
        binding.status = "REVOKED"
        binding.valid_until = utcnow()
        legacy = PlateBinding.query.filter_by(
            credential_id=credential.credential_id, status="ACTIVE"
        ).first()
        if legacy:
            legacy.status = "REVOKED"
            legacy.ended_at = utcnow()
        old_plate.status = old_status
        old_plate.physical_status = old_status
        db.session.commit()
    replacement = issue_credential(
        vehicle,
        plate_number=credential.plate_number,
        plate_code=credential.plate_code,
        reason=reason,
        authorization_reference=transaction_reference,
    )
    new_plate = physical_plate_for_credential(replacement)
    old_plate.replaced_by_id = new_plate.id
    db.session.commit()
    audit(
        event_type="PLATE_REPORTED_LOST" if old_status == "LOST" else "PLATE_REPLACED",
        result=f"OLD_PLATE_{old_status}_NEW_PLATE_ISSUED",
        risk="WARNING",
        credential_id=replacement.credential_id,
        expected=vehicle.vehicle_trust_id,
        reason=f"{reason} ({transaction_reference})",
        actor="Demo Admin",
        plate_uid=old_plate.plate_uid,
        previous_vehicle=vehicle.vehicle_trust_id,
        new_vehicle=vehicle.vehicle_trust_id,
        transaction_id=transaction_reference,
    )
    return replacement


def set_vehicle_theft_status(vehicle: Vehicle, status: str, *, reason: str) -> None:
    if status not in {"CLEAR", "REPORTED_STOLEN", "RECOVERED", "UNDER_REVIEW"}:
        raise ControlledSecurityError("Unsupported theft status")
    vehicle.theft_status = status
    db.session.commit()
    audit(
        event_type="VEHICLE_REPORTED_STOLEN"
        if status == "REPORTED_STOLEN"
        else "VEHICLE_RECOVERED",
        result=status,
        risk="CRITICAL" if status == "REPORTED_STOLEN" else "INFO",
        expected=vehicle.vehicle_trust_id,
        reason=reason,
        actor="Demo Admin",
        new_vehicle=vehicle.vehicle_trust_id,
    )


def seed_demo() -> dict[str, Vehicle]:
    if Vehicle.query.count():
        return {v.vehicle_trust_id: v for v in Vehicle.query.all()}
    owner_a = Owner(owner_reference="OWN-DEMO-A", display_name="Demo Owner A")
    owner_b = Owner(owner_reference="OWN-DEMO-B", display_name="Demo Owner B")
    db.session.add_all([owner_a, owner_b])
    db.session.commit()
    a = provision_vehicle(
        {
            "vehicle_trust_id": "VT-7A82F1",
            "full_vin": "VTO24DEMOA00034821",
            "make": "Toyota",
            "model": "Land Cruiser",
            "color": "White",
            "year": 2024,
            "vehicle_type": "Private SUV",
            "original_plate_number": "34821",
            "original_plate_code": "AH",
        }
    )
    b = provision_vehicle(
        {
            "vehicle_trust_id": "VT-91B4D7",
            "full_vin": "VTO24DEMOB00057214",
            "make": "Toyota",
            "model": "Land Cruiser",
            "color": "White",
            "year": 2024,
            "vehicle_type": "Private SUV",
            "original_plate_number": "57214",
            "original_plate_code": "BK",
        }
    )
    c = provision_vehicle(
        {
            "vehicle_trust_id": "VT-C3D8E2",
            "full_vin": "VTO25DEMOC00068432",
            "make": "Nissan",
            "model": "Patrol",
            "color": "Silver",
            "year": 2025,
            "vehicle_type": "Private SUV",
            "original_plate_number": "68432",
            "original_plate_code": "CT",
        }
    )
    db.session.add_all(
        [
            VehicleOwnership(owner_id=owner_a.id, vehicle_id=a.id),
            VehicleOwnership(owner_id=owner_a.id, vehicle_id=b.id),
            VehicleOwnership(owner_id=owner_b.id, vehicle_id=c.id),
        ]
    )
    db.session.commit()
    issue_credential(a)
    issue_credential(b)
    for credential, owner in (
        (active_credential(a.vehicle_trust_id), owner_a),
        (active_credential(b.vehicle_trust_id), owner_a),
    ):
        plate = physical_plate_for_credential(credential)
        db.session.add(
            PlateEntitlement(
                owner_id=owner.id,
                plate_number_id=plate.plate_number_id,
            )
        )
    reserved_number = PlateNumber(plate_number="77551", plate_code="DX", status="RESERVED")
    db.session.add(reserved_number)
    db.session.flush()
    db.session.add(
        PlateEntitlement(
            owner_id=owner_a.id,
            plate_number_id=reserved_number.id,
            status="RESERVED",
        )
    )
    db.session.commit()
    return {vehicle.vehicle_trust_id: vehicle for vehicle in (a, b, c)}


def reset_demo() -> None:
    db.session.remove()
    qr_dir = Path(current_app.static_folder) / "generated_qr"
    if qr_dir.exists():
        for generated_code in qr_dir.glob("VTC-*.png"):
            generated_code.unlink(missing_ok=True)
    for model in (
        AuditEvent,
        Challenge,
        RebindingHistory,
        PlateBinding,
        PlateVehicleBinding,
        PhysicalPlate,
        PlateEntitlement,
        VehicleOwnership,
        PlateNumber,
        Credential,
        Vehicle,
        Owner,
    ):
        db.session.query(model).delete(synchronize_session=False)
    db.session.commit()
    seed_demo()


def active_credential(vehicle_id: str, plate_number: str | None = None) -> Credential:
    vehicle = Vehicle.query.filter_by(vehicle_trust_id=vehicle_id).first()
    if vehicle:
        binding = (
            PlateVehicleBinding.query.filter_by(vehicle_id=vehicle.id, status="ACTIVE")
            .order_by(PlateVehicleBinding.id.desc())
            .first()
        )
        if binding:
            plate = db.session.get(PhysicalPlate, binding.physical_plate_id)
            credential = Credential.query.filter_by(
                credential_id=plate.credential_id, status="ACTIVE"
            ).first()
            if credential and (not plate_number or credential.plate_number == plate_number):
                return credential
    query = Credential.query.filter_by(vehicle_trust_id=vehicle_id, status="ACTIVE")
    if plate_number:
        query = query.filter_by(plate_number=plate_number)
    return query.order_by(Credential.id.desc()).first()


def run_scenario(name: str, *, reset: bool = True) -> dict:
    if reset:
        reset_demo()
    a = Vehicle.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    b = Vehicle.query.filter_by(vehicle_trust_id="VT-91B4D7").one()
    cred_a = active_credential(a.vehicle_trust_id)
    content = credential_content(cred_a)
    if name == "normal":
        actual = verify_vehicle(content, a.vehicle_trust_id)
        expected = "VERIFIED"
    elif name == "clone":
        actual = verify_vehicle(
            content, b.vehicle_trust_id, mismatch_result="VEHICLE_IDENTITY_MISMATCH"
        )
        expected = "VEHICLE_IDENTITY_MISMATCH"
    elif name == "swap":
        actual = verify_vehicle(
            content, b.vehicle_trust_id, mismatch_result="GENUINE_PLATE_WRONG_VEHICLE"
        )
        expected = "GENUINE_PLATE_WRONG_VEHICLE"
    elif name == "tamper":
        tampered = tamper_code_field(content, 1, 2)
        actual = verify_vehicle(tampered, a.vehicle_trust_id)
        expected = "INVALID_DIGITAL_SIGNATURE"
    elif name == "impersonation":
        payload = json.loads(cred_a.payload_json)
        challenge = create_challenge(payload)
        module_b = SimulatedVehicleSecureModule(b.secure_key_ref, b.secure_module_status)
        signature_b = module_b.sign_challenge(challenge.payload_json.encode())
        actual = submit_challenge_response(challenge, a.vehicle_trust_id, signature_b)
        expected = "INVALID_VEHICLE_PROOF"
    elif name == "replay":
        first = verify_vehicle(content, a.vehicle_trust_id)
        challenge = Challenge.query.filter_by(challenge_id=first["challenge_id"]).one()
        actual = submit_challenge_response(
            challenge, a.vehicle_trust_id, challenge.vehicle_signature_b64
        )
        expected = "REPLAY_DETECTED"
    elif name == "expiry":
        actual = verify_vehicle(content, a.vehicle_trust_id, expired_challenge=True)
        expected = "EXPIRED_CHALLENGE"
    elif name == "revocation":
        revoke_credential(cred_a)
        actual = verify_vehicle(content, a.vehicle_trust_id)
        expected = "CREDENTIAL_REVOKED"
    elif name == "rebinding":
        new_credential = authorized_rebind(
            cred_a,
            b,
            reason="Authorized hackathon demonstration transfer",
            authorization_reference="DEMO-REBIND-2026-001",
        )
        actual = verify_vehicle(credential_content(new_credential), b.vehicle_trust_id)
        expected = "VERIFIED"
        actual["new_credential_id"] = new_credential.credential_id
    elif name == "offline":
        a.secure_module_status = "OFFLINE"
        db.session.commit()
        actual = verify_vehicle(content, a.vehicle_trust_id)
        a.secure_module_status = "ONLINE"
        db.session.commit()
        expected = "SECURE_MODULE_UNAVAILABLE"
    elif name == "stolen":
        set_vehicle_theft_status(a, "REPORTED_STOLEN", reason="Security Lab scenario")
        actual = verify_vehicle(content, a.vehicle_trust_id)
        expected = "VERIFIED_IDENTITY_STOLEN_VEHICLE"
    else:
        raise ControlledSecurityError("Unknown security lab scenario")
    controls = {
        "normal": "Issuer signature + fresh vehicle proof + registry binding",
        "clone": "Fresh vehicle proof and plate-to-vehicle binding",
        "swap": "Authentic credential separated from live vehicle identity",
        "tamper": "Canonical CBOR + COSE_Sign1 ES256 signature",
        "impersonation": "Independent vehicle key verification",
        "replay": "One-time challenge ID and persisted consumption state",
        "expiry": "Challenge TTL enforcement",
        "revocation": "Operational credential status",
        "rebinding": "Authorized evidence-preserving credential replacement",
        "offline": "Mandatory dependency fail-closed policy",
        "stolen": "Identity assurance separated from operational theft status",
    }
    return {
        "scenario": name,
        "expected": expected,
        "actual": actual["result"],
        "passed": actual["result"] == expected,
        "control": controls[name],
        "details": actual,
    }


def run_full_demo() -> dict:
    names = [
        "normal",
        "clone",
        "swap",
        "tamper",
        "impersonation",
        "replay",
        "expiry",
        "offline",
        "revocation",
        "rebinding",
        "stolen",
    ]
    lifecycle_names = [
        "keep_plate",
        "sell_vehicle_with_plate",
        "sell_vehicle_keep_plate",
        "sell_plate_number",
        "lost_plate",
        "multiple_vehicles",
        "duplicate_binding",
        "stolen_vehicle",
        "plate_replacement",
        "concurrent_rebinding",
    ]
    from . import create_app

    sandbox = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "GENERATE_QR_IMAGES": False,
        }
    )
    with sandbox.app_context():
        results = [run_scenario(name, reset=True) for name in names]
        lifecycle_results = [run_lifecycle_scenario(name, reset=True) for name in lifecycle_names]
    all_results = results + lifecycle_results
    reset_demo()
    for item in all_results:
        db.session.add(
            AuditEvent(
                event_id=f"EVT-{uuid.uuid4().hex[:12].upper()}",
                event_type="FULL_DEMO_SCENARIO",
                result=item["actual"],
                reason=(
                    f"{item['scenario']}: expected {item['expected']}; actual {item['actual']}"
                ),
                risk_level="INFO" if item["passed"] else "CRITICAL",
                timeline_json=json.dumps(["Deterministic sandbox execution", "Result compared"]),
            )
        )
    db.session.commit()
    return {
        "count": len(all_results),
        "passed": all(item["passed"] for item in all_results),
        "results": results,
        "lifecycle_results": lifecycle_results,
    }


def run_lifecycle_scenario(name: str, *, reset: bool = True) -> dict:
    if reset:
        reset_demo()
    a = Vehicle.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    b = Vehicle.query.filter_by(vehicle_trust_id="VT-91B4D7").one()
    c = Vehicle.query.filter_by(vehicle_trust_id="VT-C3D8E2").one()
    owner_a = Owner.query.filter_by(owner_reference="OWN-DEMO-A").one()
    owner_b = Owner.query.filter_by(owner_reference="OWN-DEMO-B").one()
    credential = active_credential(a.vehicle_trust_id)
    old_code = credential_content(credential)
    old_uid = credential.plate_serial
    details: dict = {}
    if name == "keep_plate":
        rebound = authorized_rebind(
            credential,
            b,
            reason="Owner keeps plate for a replacement vehicle",
            authorization_reference="LC-001",
        )
        result = verify_vehicle(credential_content(rebound), b.vehicle_trust_id)["result"]
        actual, expected = (
            "REBIND_SUCCESS_STATIC_CODE"
            if result == "VERIFIED"
            and credential_content(rebound) == old_code
            and rebound.plate_serial == old_uid
            else result,
            "REBIND_SUCCESS_STATIC_CODE",
        )
    elif name == "sell_vehicle_with_plate":
        transfer_vehicle_ownership(a, owner_b, transaction_reference="LC-002")
        result = verify_vehicle(old_code, a.vehicle_trust_id)["result"]
        actual, expected = (
            "OWNERSHIP_CHANGED_BINDING_REMAINS" if result == "VERIFIED" else result,
            "OWNERSHIP_CHANGED_BINDING_REMAINS",
        )
    elif name == "sell_vehicle_keep_plate":
        reserve_physical_plate(
            credential, reason="Vehicle sold while plate retained", transaction_reference="LC-003"
        )
        result = verify_vehicle(old_code, a.vehicle_trust_id)["result"]
        actual, expected = result, "RESERVED_PLATE"
    elif name == "sell_plate_number":
        replacement = transfer_plate_number(credential, owner_b, c, transaction_reference="LC-004")
        old_result = verify_vehicle(old_code, a.vehicle_trust_id)["result"]
        new_result = verify_vehicle(credential_content(replacement), c.vehicle_trust_id)["result"]
        details = {
            "old_result": old_result,
            "new_result": new_result,
            "old_plate_uid": old_uid,
            "new_plate_uid": replacement.plate_serial,
        }
        actual = (
            "OLD_PLATE_RETIRED_NEW_PLATE_ISSUED"
            if old_result == "RETIRED_PHYSICAL_PLATE" and new_result == "VERIFIED"
            else f"{old_result}/{new_result}"
        )
        expected = "OLD_PLATE_RETIRED_NEW_PLATE_ISSUED"
    elif name == "lost_plate":
        replacement = reissue_physical_plate(
            credential,
            old_status="LOST",
            reason="Physical plate reported lost",
            transaction_reference="LC-005",
        )
        old_result = verify_vehicle(old_code, a.vehicle_trust_id)["result"]
        new_result = verify_vehicle(credential_content(replacement), a.vehicle_trust_id)["result"]
        details = {"old_result": old_result, "new_result": new_result}
        actual = (
            "OLD_PLATE_LOST_NEW_PLATE_ISSUED"
            if old_result == "LOST_PLATE" and new_result == "VERIFIED"
            else f"{old_result}/{new_result}"
        )
        expected = "OLD_PLATE_LOST_NEW_PLATE_ISSUED"
    elif name == "multiple_vehicles":
        ownerships = VehicleOwnership.query.filter_by(owner_id=owner_a.id, status="ACTIVE").count()
        bindings = PlateVehicleBinding.query.filter(
            PlateVehicleBinding.vehicle_id.in_([a.id, b.id]), PlateVehicleBinding.status == "ACTIVE"
        ).count()
        actual = (
            "INDEPENDENT_ACTIVE_BINDINGS"
            if ownerships == 2 and bindings == 2
            else "INTEGRITY_FAILURE"
        )
        expected = "INDEPENDENT_ACTIVE_BINDINGS"
    elif name == "duplicate_binding":
        plate = physical_plate_for_credential(credential)
        db.session.add(
            PlateVehicleBinding(
                physical_plate_id=plate.id,
                vehicle_id=c.id,
                reason="Negative duplicate test",
                transaction_reference="LC-007",
            )
        )
        try:
            db.session.commit()
            actual = "DUPLICATE_ALLOWED"
        except IntegrityError:
            db.session.rollback()
            actual = "BLOCKED"
        expected = "BLOCKED"
    elif name == "stolen_vehicle":
        set_vehicle_theft_status(a, "REPORTED_STOLEN", reason="LC-008")
        actual = verify_vehicle(old_code, a.vehicle_trust_id)["result"]
        expected = "VERIFIED_IDENTITY_STOLEN_VEHICLE"
    elif name == "plate_replacement":
        replacement = reissue_physical_plate(
            credential,
            old_status="REPLACED",
            reason="Damaged plate replacement",
            transaction_reference="LC-009",
        )
        old_result = verify_vehicle(old_code, a.vehicle_trust_id)["result"]
        new_result = verify_vehicle(credential_content(replacement), a.vehicle_trust_id)["result"]
        actual = (
            "OLD_PLATE_REPLACED_NEW_PLATE_ISSUED"
            if old_result == "REVOKED_PLATE" and new_result == "VERIFIED"
            else f"{old_result}/{new_result}"
        )
        expected = "OLD_PLATE_REPLACED_NEW_PLATE_ISSUED"
    elif name == "concurrent_rebinding":
        authorized_rebind(
            credential,
            b,
            reason="First competing transaction",
            authorization_reference="LC-010-A",
        )
        try:
            authorized_rebind(
                credential,
                c,
                reason="Second competing transaction",
                authorization_reference="LC-010-B",
            )
            actual = "BOTH_SUCCEEDED"
        except ControlledSecurityError:
            actual = "ONE_TRANSACTION_ONLY"
        expected = "ONE_TRANSACTION_ONLY"
    else:
        raise ControlledSecurityError("Unknown lifecycle scenario")
    return {
        "scenario": name,
        "expected": expected,
        "actual": actual,
        "passed": actual == expected,
        "details": details,
    }
