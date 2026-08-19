"""Compact signed visual credential using canonical CBOR and COSE_Sign1 semantics."""

import base64

import cbor2
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)

CODE_PREFIX = "VT1:"
COSE_SIGN1_TAG = 18
COSE_HEADER_ALG = 1
COSE_HEADER_KID = 4
COSE_ALG_ES256 = -7
ISSUER_KID = b"VTO1"
PAYLOAD_KEYS = {1, 2, 3}


class CompactCredentialError(ValueError):
    pass


class CompactSignatureError(CompactCredentialError):
    pass


def _base45_encode(data: bytes) -> str:
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
    output: list[str] = []
    index = 0
    while index < len(data):
        if index + 1 < len(data):
            value = data[index] * 256 + data[index + 1]
            output.extend(
                [alphabet[value % 45], alphabet[(value // 45) % 45], alphabet[value // 2025]]
            )
            index += 2
        else:
            value = data[index]
            output.extend([alphabet[value % 45], alphabet[value // 45]])
            index += 1
    return "".join(output)


def _base45_decode(text: str) -> bytes:
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
    lookup = {character: index for index, character in enumerate(alphabet)}
    output = bytearray()
    index = 0
    try:
        while index < len(text):
            remaining = len(text) - index
            if remaining >= 3:
                value = (
                    lookup[text[index]]
                    + lookup[text[index + 1]] * 45
                    + lookup[text[index + 2]] * 2025
                )
                if value > 65535:
                    raise CompactCredentialError("Invalid Base45 value")
                output.extend(divmod(value, 256))
                index += 3
            elif remaining == 2:
                value = lookup[text[index]] + lookup[text[index + 1]] * 45
                if value > 255:
                    raise CompactCredentialError("Invalid Base45 tail")
                output.append(value)
                index += 2
            else:
                raise CompactCredentialError("Truncated Base45 data")
    except KeyError as exc:
        raise CompactCredentialError("Invalid Base45 character") from exc
    return bytes(output)


def compact_fields(payload: dict) -> dict:
    try:
        credential_hex = payload["credential_id"].removeprefix("VTC-")
        serial_hex = payload["plate_serial"].removeprefix("PLT-OM-")
        return {
            1: int(payload["version"]),
            2: bytes.fromhex(credential_hex),
            3: bytes.fromhex(serial_hex),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise CompactCredentialError("Credential cannot be compacted") from exc


def _signature_structure(protected: bytes, payload_bytes: bytes) -> bytes:
    return cbor2.dumps(["Signature1", protected, b"", payload_bytes], canonical=True)


def _build_cose_bytes(fields: dict, raw_signature: bytes) -> bytes:
    protected = cbor2.dumps({COSE_HEADER_ALG: COSE_ALG_ES256}, canonical=True)
    payload_bytes = cbor2.dumps(fields, canonical=True)
    sign1 = cbor2.CBORTag(
        COSE_SIGN1_TAG,
        [protected, {COSE_HEADER_KID: ISSUER_KID}, payload_bytes, raw_signature],
    )
    return cbor2.dumps(sign1, canonical=True)


def _build_code(fields: dict, raw_signature: bytes) -> str:
    return CODE_PREFIX + _base45_encode(_build_cose_bytes(fields, raw_signature))


def create_signed_code(payload: dict, authority) -> tuple[str, str]:
    fields = compact_fields(payload)
    protected = cbor2.dumps({COSE_HEADER_ALG: COSE_ALG_ES256}, canonical=True)
    payload_bytes = cbor2.dumps(fields, canonical=True)
    der_signature = authority.sign_bytes(_signature_structure(protected, payload_bytes))
    r_value, s_value = decode_dss_signature(der_signature)
    raw_signature = r_value.to_bytes(32, "big") + s_value.to_bytes(32, "big")
    return _build_code(fields, raw_signature), base64.b64encode(raw_signature).decode()


def code_from_credential(credential) -> str:
    fields = compact_fields(
        {
            "credential_id": credential.credential_id,
            "plate_serial": credential.plate_serial,
            "version": credential.version,
        }
    )
    try:
        signature = base64.b64decode(credential.signature_b64, validate=True)
    except ValueError as exc:
        raise CompactCredentialError("Stored credential signature is malformed") from exc
    return _build_code(fields, signature)


def binary_code_from_credential(credential) -> bytes:
    fields = compact_fields(
        {
            "credential_id": credential.credential_id,
            "plate_serial": credential.plate_serial,
            "version": credential.version,
        }
    )
    try:
        signature = base64.b64decode(credential.signature_b64, validate=True)
    except ValueError as exc:
        raise CompactCredentialError("Stored credential signature is malformed") from exc
    return _build_cose_bytes(fields, signature)


def _decode_envelope_bytes(raw_code: bytes) -> tuple[bytes, dict, bytes, bytes]:
    try:
        decoded = cbor2.loads(raw_code)
    except (cbor2.CBORDecodeError, TypeError, ValueError) as exc:
        raise CompactCredentialError("Malformed compact credential") from exc
    if not isinstance(decoded, cbor2.CBORTag) or decoded.tag != COSE_SIGN1_TAG:
        raise CompactCredentialError("Credential is not COSE_Sign1")
    if not isinstance(decoded.value, list) or len(decoded.value) != 4:
        raise CompactCredentialError("Malformed COSE_Sign1 envelope")
    protected, unprotected, payload_bytes, raw_signature = decoded.value
    if not all(isinstance(item, bytes) for item in (protected, payload_bytes, raw_signature)):
        raise CompactCredentialError("Invalid COSE binary fields")
    try:
        protected_map = cbor2.loads(protected)
        fields = cbor2.loads(payload_bytes)
    except (cbor2.CBORDecodeError, TypeError, ValueError) as exc:
        raise CompactCredentialError("Invalid canonical CBOR") from exc
    if protected_map != {COSE_HEADER_ALG: COSE_ALG_ES256}:
        raise CompactCredentialError("Unsupported signature algorithm")
    if unprotected != {COSE_HEADER_KID: ISSUER_KID}:
        raise CompactCredentialError("Unknown issuer key identifier")
    if not isinstance(fields, dict) or set(fields) != PAYLOAD_KEYS:
        raise CompactCredentialError("Invalid compact payload fields")
    if len(raw_signature) != 64:
        raise CompactCredentialError("Invalid ES256 signature length")
    return protected, fields, payload_bytes, raw_signature


def _decode_envelope(code: str) -> tuple[bytes, dict, bytes, bytes]:
    if not isinstance(code, str) or not code.startswith(CODE_PREFIX):
        raise CompactCredentialError("Unsupported compact credential prefix")
    return _decode_envelope_bytes(_base45_decode(code[len(CODE_PREFIX) :]))


def _verify_envelope(envelope: tuple[bytes, dict, bytes, bytes], authority) -> dict:
    protected, fields, payload_bytes, raw_signature = envelope
    r_value = int.from_bytes(raw_signature[:32], "big")
    s_value = int.from_bytes(raw_signature[32:], "big")
    der_signature = encode_dss_signature(r_value, s_value)
    if not authority.verify_bytes(_signature_structure(protected, payload_bytes), der_signature):
        raise CompactSignatureError("Invalid digital signature")
    version, credential_bytes, serial_bytes = fields[1], fields[2], fields[3]
    if version != 1 or len(credential_bytes) != 8 or len(serial_bytes) != 6:
        raise CompactCredentialError("Invalid compact credential values")
    return {
        "version": version,
        "credential_id": f"VTC-{credential_bytes.hex().upper()}",
        "issuer_id": ISSUER_KID.decode(),
        "plate_serial": f"PLT-OM-{serial_bytes.hex().upper()}",
        "payload_bytes": len(payload_bytes),
    }


def decode_and_verify_code(code: str, authority) -> dict:
    reference = _verify_envelope(_decode_envelope(code), authority)
    reference["transport_bytes"] = len(code.encode())
    return reference


def decode_and_verify_bytes(raw_code: bytes, authority) -> dict:
    reference = _verify_envelope(_decode_envelope_bytes(raw_code), authority)
    reference["encoded_bytes"] = len(raw_code)
    return reference


def tamper_code_field(code: str, key: int, value) -> str:
    """Security Lab helper: alter protected CBOR while retaining the original signature."""
    _, fields, _, signature = _decode_envelope(code)
    fields[key] = value
    return _build_code(fields, signature)
