import base64

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from vehicletrust.crypto import DemoIssuerAuthority, canonical_json, generate_key_pair
from vehicletrust.models import Credential, Vehicle


def test_issuer_valid_modified_wrong_and_malformed(app, ctx):
    authority = DemoIssuerAuthority(app.instance_path)
    payload = {"credential_id": "TEST", "value": "original"}
    signature = authority.sign(payload)
    assert authority.verify(payload, signature)
    assert not authority.verify({**payload, "value": "modified"}, signature)
    assert not authority.verify(payload, signature[:-8])
    assert not authority.verify(payload, "not-base64!@")
    _, wrong_public = generate_key_pair()
    wrong_key = serialization.load_pem_public_key(wrong_public)
    with pytest.raises(InvalidSignature):
        wrong_key.verify(
            base64.b64decode(signature), canonical_json(payload), ec.ECDSA(hashes.SHA256())
        )


def test_private_keys_never_exposed(client, ctx):
    for path in ["/", "/dashboard", "/vehicles", "/verify", "/security-lab", "/api/lab/normal"]:
        response = client.post(path) if path.startswith("/api/") else client.get(path)
        assert b"PRIVATE KEY" not in response.data.upper()
        assert b"BEGIN PRIVATE KEY" not in response.data
    assert not hasattr(Vehicle, "private_key")
    assert not hasattr(Credential, "private_key")
