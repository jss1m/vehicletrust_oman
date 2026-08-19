import base64
import hashlib
import json
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

ISSUER_NAME = "VehicleTrust Oman Demo Authority"


def canonical_json(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fingerprint(public_pem: str | bytes) -> str:
    raw = public_pem.encode() if isinstance(public_pem, str) else public_pem
    key = serialization.load_pem_public_key(raw)
    der = key.public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return hashlib.sha256(der).hexdigest().upper()


def generate_key_pair() -> tuple[bytes, bytes]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


class DemoIssuerAuthority:
    def __init__(self, instance_path: str):
        root = Path(instance_path) / "issuer"
        root.mkdir(parents=True, exist_ok=True)
        self._private_path = root / "issuer_private.pem"
        self.public_path = root / "issuer_public.pem"
        if not self._private_path.exists():
            private_pem, public_pem = generate_key_pair()
            self._private_path.write_bytes(private_pem)
            self.public_path.write_bytes(public_pem)

    def sign(self, payload: dict) -> str:
        signature = self.sign_bytes(canonical_json(payload))
        return base64.b64encode(signature).decode()

    def sign_bytes(self, payload: bytes) -> bytes:
        private_key = serialization.load_pem_private_key(
            self._private_path.read_bytes(), password=None
        )
        return private_key.sign(payload, ec.ECDSA(hashes.SHA256()))

    def verify(self, payload: dict, signature_b64: str) -> bool:
        try:
            signature = base64.b64decode(signature_b64, validate=True)
            return self.verify_bytes(canonical_json(payload), signature)
        except (InvalidSignature, ValueError, TypeError):
            return False

    def verify_bytes(self, payload: bytes, signature: bytes) -> bool:
        try:
            public_key = serialization.load_pem_public_key(self.public_path.read_bytes())
            public_key.verify(signature, payload, ec.ECDSA(hashes.SHA256()))
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False

    @property
    def public_key_fingerprint(self) -> str:
        return fingerprint(self.public_path.read_bytes())
