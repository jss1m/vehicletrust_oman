# Security Test Matrix

All actual results were executed; none are assumed.

| ID | Threat | Setup | Expected | Actual | Automated | E2E / screenshot | Status |
|---|---|---|---|---|---|---|---|
| VT-001 | Normal | Plate A + Vehicle A | VERIFIED | VERIFIED | PASS | `05_vehicle_verified.png` | PASS |
| VT-002 | Protected-byte modification | Change canonical CBOR without signing | INVALID_DIGITAL_SIGNATURE | INVALID_DIGITAL_SIGNATURE | PASS | `08_tamper_detected.png` | PASS |
| VT-003 | Clone | Exact code A + Vehicle B | VEHICLE_IDENTITY_MISMATCH | VEHICLE_IDENTITY_MISMATCH | PASS | `07_credential_clone_detected.png` | PASS |
| VT-004 | Genuine plate swap | Authentic Plate A + Vehicle B | GENUINE_PLATE_WRONG_VEHICLE | GENUINE_PLATE_WRONG_VEHICLE | PASS | `06_genuine_plate_wrong_vehicle.png` | PASS |
| VT-005 | Impersonation | B proof claimed as A | INVALID_VEHICLE_PROOF | INVALID_VEHICLE_PROOF | PASS | Lab/full demo | PASS |
| VT-006 | Replay | Reuse consumed response | REPLAY_DETECTED | REPLAY_DETECTED | PASS | `09_replay_detected.png` | PASS |
| VT-007 | Expiry | Submit after controlled TTL | EXPIRED_CHALLENGE | EXPIRED_CHALLENGE | PASS | Full demo | PASS |
| VT-008 | Revocation | Valid signature, revoked registry state | CREDENTIAL_REVOKED | CREDENTIAL_REVOKED | PASS | Full demo | PASS |
| VT-009 | Authorized rebind | Static Plate UID A from vehicle A to B | VERIFIED | VERIFIED | PASS | `10_rebinding_verified.png` | PASS |
| VT-010 | Unknown vehicle | Unregistered responder identity | UNKNOWN_VEHICLE | UNKNOWN_VEHICLE | PASS | API corpus | PASS |
| VT-011 | Malformed credential | Empty/random/truncated/oversized/version corpus | controlled deny | TAMPERED_CREDENTIAL / controlled deny | PASS | API corpus | PASS |
| VT-012 | Secure module offline | Required signer unavailable | SECURE_MODULE_UNAVAILABLE | SECURE_MODULE_UNAVAILABLE | PASS | Full demo | PASS |

The lifecycle extension LC-001–LC-010 is recorded in `VEHICLETRUST_VALIDATION_MATRIX.md`. Security invariants cover invalid signatures, revoked/reserved/lost/retired states, independent keys, replay/expiry, genuine wrong-vehicle placement, dependency failure, static-code rebind history, rollback, and concurrent-binding protection.
