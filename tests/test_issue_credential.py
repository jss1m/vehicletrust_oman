import json
from pathlib import Path

import cv2
import pytest

from vehicletrust.credential_code import (
    CompactCredentialError,
    binary_code_from_credential,
    decode_and_verify_bytes,
    decode_and_verify_code,
    tamper_code_field,
)
from vehicletrust.crypto import ISSUER_NAME, canonical_json
from vehicletrust.models import Challenge, Credential, Vehicle
from vehicletrust.services import (
    ControlledSecurityError,
    credential_content,
    issue_credential,
    issuer,
    verify_vehicle,
)


def test_issue_compact_credential_and_image_round_trip(app, ctx):
    vehicle = Vehicle.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    credential = issue_credential(vehicle, plate_number="68432", plate_code="CT")
    payload = json.loads(credential.payload_json)
    code = credential_content(credential)
    reference = decode_and_verify_code(code, issuer())

    assert payload["credential_id"] == credential.credential_id
    assert payload["plate_serial"] == credential.plate_serial
    assert payload["vehicle_trust_id"] == vehicle.vehicle_trust_id
    assert payload["issuer"] == ISSUER_NAME
    assert payload["vehicle_public_key_fingerprint"] == vehicle.public_key_fingerprint
    assert canonical_json(payload) == canonical_json(dict(reversed(list(payload.items()))))
    assert code.startswith("VT1:")
    assert len(binary_code_from_credential(credential)) == 101
    assert len(code.encode()) < 200
    assert reference["credential_id"] == credential.credential_id
    assert reference["plate_serial"] == credential.plate_serial
    assert reference["issuer_id"] == "VTO1"

    image_path = Path(app.static_folder) / "generated_qr" / credential.qr_filename
    image = cv2.imread(str(image_path))
    decoded_utf8, _, _ = cv2.QRCodeDetector().detectAndDecodeBytes(image)
    decoded = decoded_utf8.decode("utf-8").encode("latin1")
    assert decoded == binary_code_from_credential(credential)
    assert decode_and_verify_bytes(decoded, issuer())["credential_id"] == credential.credential_id


def test_visual_code_minimum_reliable_size_is_recorded(app, ctx):
    credential = Credential.query.filter_by(vehicle_trust_id="VT-7A82F1").first()
    expected = binary_code_from_credential(credential)
    image_path = Path(app.static_folder) / "generated_qr" / credential.qr_filename
    image = cv2.imread(str(image_path))
    minimum = None
    for size in range(60, 121, 4):
        resized = cv2.resize(image, (size, size), interpolation=cv2.INTER_NEAREST)
        decoded_utf8, _, _ = cv2.QRCodeDetector().detectAndDecodeBytes(resized)
        if decoded_utf8:
            decoded = decoded_utf8.decode("utf-8").encode("latin1")
            if decoded == expected:
                minimum = size
                break
    assert minimum is not None
    assert minimum <= 112


def test_corrupted_code_image_and_data_are_rejected(app, ctx):
    credential = Credential.query.filter_by(vehicle_trust_id="VT-7A82F1").first()
    code = credential_content(credential)
    tampered = tamper_code_field(code, 1, 2)
    with pytest.raises(CompactCredentialError, match="signature"):
        decode_and_verify_code(tampered, issuer())
    result = verify_vehicle(tampered, "VT-7A82F1")
    assert result["result"] == "INVALID_DIGITAL_SIGNATURE"
    assert Challenge.query.count() == 0

    image_path = Path(app.static_folder) / "generated_qr" / credential.qr_filename
    image = cv2.imread(str(image_path))
    image[:, : image.shape[1] // 2] = 255
    decoded, _, _ = cv2.QRCodeDetector().detectAndDecodeBytes(image)
    assert not decoded
    assert verify_vehicle("", "VT-7A82F1")["result"] == "TAMPERED_CREDENTIAL"


def test_duplicate_active_plate_binding_rejected(ctx):
    vehicle = Vehicle.query.filter_by(vehicle_trust_id="VT-91B4D7").one()
    with pytest.raises(ControlledSecurityError, match="Duplicate"):
        issue_credential(vehicle, plate_number="34821", plate_code="AH")


def test_credential_ids_and_serials_unique(ctx):
    credentials = Credential.query.all()
    assert len({item.credential_id for item in credentials}) == len(credentials)
    assert len({item.plate_serial for item in credentials}) == len(credentials)
