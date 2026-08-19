import json

import pytest

from vehicletrust.credential_code import create_signed_code, tamper_code_field
from vehicletrust.models import Vehicle
from vehicletrust.services import (
    active_credential,
    credential_content,
    issuer,
    verify_vehicle,
)


@pytest.mark.parametrize(
    "content",
    ["", "random text", "VT1:", "VT1:%%%", "VT1:A", "{", "[]"],
)
def test_malformed_credentials_fail_controlled(ctx, content):
    result = verify_vehicle(content, "VT-7A82F1")
    assert result["result"] == "TAMPERED_CREDENTIAL"


def test_oversized_input_fails_controlled(ctx):
    assert verify_vehicle("x" * 20_000, "VT-7A82F1")["result"] == "TAMPERED_CREDENTIAL"


def test_signed_but_unsupported_version_is_controlled(ctx):
    credential = active_credential("VT-7A82F1")
    payload = json.loads(credential.payload_json)
    payload["version"] = 99
    code, _ = create_signed_code(payload, issuer())
    result = verify_vehicle(code, "VT-7A82F1")
    assert result["result"] == "TAMPERED_CREDENTIAL"


def test_modified_compact_field_is_invalid_signature(ctx):
    code = credential_content(active_credential("VT-7A82F1"))
    assert verify_vehicle(tamper_code_field(code, 1, 99), "VT-7A82F1")["result"] == (
        "INVALID_DIGITAL_SIGNATURE"
    )


def test_unknown_vehicle_is_distinct(ctx):
    content = credential_content(active_credential("VT-7A82F1"))
    assert verify_vehicle(content, "VT-000000")["result"] == "UNKNOWN_VEHICLE"


def test_registered_keys_are_independent(ctx):
    a = Vehicle.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    b = Vehicle.query.filter_by(vehicle_trust_id="VT-91B4D7").one()
    assert a.public_key_fingerprint != b.public_key_fingerprint
