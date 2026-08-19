import base64
import json

from vehicletrust.extensions import db
from vehicletrust.models import Vehicle
from vehicletrust.services import (
    active_credential,
    create_challenge,
    credential_content,
    submit_challenge_response,
    verify_vehicle,
)


def test_secure_module_offline_fails_closed(ctx):
    vehicle = Vehicle.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    vehicle.secure_module_status = "OFFLINE"
    db.session.commit()
    result = verify_vehicle(
        credential_content(active_credential(vehicle.vehicle_trust_id)), vehicle.vehicle_trust_id
    )
    assert result["result"] == "SECURE_MODULE_UNAVAILABLE"


def test_malformed_vehicle_signature_and_missing_public_key_fail_closed(ctx):
    credential = active_credential("VT-7A82F1")
    payload = json.loads(credential.payload_json)
    challenge = create_challenge(payload)
    assert (
        submit_challenge_response(challenge, "VT-7A82F1", base64.b64encode(b"bad").decode())[
            "result"
        ]
        == "INVALID_VEHICLE_PROOF"
    )
    vehicle = Vehicle.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    vehicle.public_key_pem = None
    db.session.commit()
    challenge = create_challenge(payload)
    assert (
        submit_challenge_response(challenge, "VT-7A82F1", base64.b64encode(b"bad").decode())[
            "result"
        ]
        == "INVALID_VEHICLE_PROOF"
    )


def test_expired_credential_and_unknown_issuer_denied(ctx):
    from vehicletrust.models import Vehicle
    from vehicletrust.services import issue_credential

    vehicle = Vehicle.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    credential = issue_credential(vehicle, plate_number="68435", plate_code="CZ", years=0)
    assert (
        verify_vehicle(credential_content(credential), "VT-7A82F1")["result"]
        == "EXPIRED_CREDENTIAL"
    )
    active = active_credential("VT-91B4D7")
    active.issuer = "Unknown Demo Issuer"
    db.session.commit()
    assert verify_vehicle(credential_content(active), "VT-91B4D7")["result"] == "UNKNOWN_ISSUER"


def test_admin_operations_are_not_public(client, ctx):
    credential = active_credential("VT-7A82F1")
    response = client.post(f"/api/admin/credentials/{credential.credential_id}/revoke")
    assert response.status_code == 403
    response = client.post("/api/admin/reset")
    assert response.status_code == 403
