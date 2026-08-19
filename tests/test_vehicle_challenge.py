import base64

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from vehicletrust.models import Vehicle
from vehicletrust.secure_module import SimulatedVehicleSecureModule, VehicleSecureModule


def test_independent_vehicle_keys_and_isolation(ctx):
    a = Vehicle.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    b = Vehicle.query.filter_by(vehicle_trust_id="VT-91B4D7").one()
    module_a = SimulatedVehicleSecureModule(a.secure_key_ref)
    challenge = b"fresh challenge A"
    signature = base64.b64decode(module_a.sign_challenge(challenge))
    public_a = serialization.load_pem_public_key(a.public_key_pem.encode())
    public_b = serialization.load_pem_public_key(b.public_key_pem.encode())
    public_a.verify(signature, challenge, ec.ECDSA(hashes.SHA256()))
    with pytest.raises(InvalidSignature):
        public_b.verify(signature, challenge, ec.ECDSA(hashes.SHA256()))
    assert a.public_key_fingerprint != b.public_key_fingerprint
    assert "get_private_key" not in VehicleSecureModule.__dict__
    assert not hasattr(module_a, "get_private_key")


def test_changed_challenge_has_different_signature(ctx):
    a = Vehicle.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
    module = SimulatedVehicleSecureModule(a.secure_key_ref)
    assert module.sign_challenge(b"nonce-one") != module.sign_challenge(b"nonce-two")
