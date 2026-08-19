import base64
from abc import ABC, abstractmethod
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .crypto import generate_key_pair


class VehicleSecureModule(ABC):
    @abstractmethod
    def sign_challenge(self, challenge: bytes) -> str: ...

    @abstractmethod
    def get_public_identity(self) -> str: ...

    @abstractmethod
    def get_status(self) -> str: ...


class SimulatedVehicleSecureModule(VehicleSecureModule):
    def __init__(self, key_reference: str, status: str = "ONLINE"):
        self._key_path = Path(key_reference)
        self._status = status

    @classmethod
    def provision(cls, instance_path: str, vehicle_trust_id: str) -> tuple[str, str]:
        directory = Path(instance_path) / "vehicle_keys"
        directory.mkdir(parents=True, exist_ok=True)
        key_path = directory / f"{vehicle_trust_id}.pem"
        if key_path.exists():
            private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
            public_pem = private_key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            return str(key_path), public_pem.decode()
        private_pem, public_pem = generate_key_pair()
        key_path.write_bytes(private_pem)
        return str(key_path), public_pem.decode()

    def sign_challenge(self, challenge: bytes) -> str:
        if self._status != "ONLINE" or not self._key_path.exists():
            raise RuntimeError("Secure vehicle module unavailable")
        private_key = serialization.load_pem_private_key(self._key_path.read_bytes(), password=None)
        signature = private_key.sign(challenge, ec.ECDSA(hashes.SHA256()))
        return base64.b64encode(signature).decode()

    def get_public_identity(self) -> str:
        private_key = serialization.load_pem_private_key(self._key_path.read_bytes(), password=None)
        return (
            private_key.public_key()
            .public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode()
        )

    def get_status(self) -> str:
        return self._status


class ESP32SecureElementVehicleModule(VehicleSecureModule):
    """Future adapter contract; intentionally not connected in the software MVP."""

    def sign_challenge(self, challenge: bytes) -> str:
        raise NotImplementedError("Hardware adapter not configured")

    def get_public_identity(self) -> str:
        raise NotImplementedError("Hardware adapter not configured")

    def get_status(self) -> str:
        return "NOT_CONFIGURED"
