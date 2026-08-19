# Hadatha Security Test Matrix

| ID | Threat / lifecycle | Expected | Actual | Automated | Browser evidence | Status |
|---|---|---|---|---|---|---|
| VT-001 | Normal | VERIFIED | VERIFIED | Yes | Yes | PASS |
| VT-002 | Modified credential | INVALID_DIGITAL_SIGNATURE | INVALID_DIGITAL_SIGNATURE | Yes | Yes | PASS |
| VT-003 | Clone | VEHICLE_IDENTITY_MISMATCH | VEHICLE_IDENTITY_MISMATCH | Yes | Yes | PASS |
| VT-004 | Genuine swap | GENUINE_PLATE_WRONG_VEHICLE | GENUINE_PLATE_WRONG_VEHICLE | Yes | Yes | PASS |
| VT-005 | Impersonation | INVALID_VEHICLE_PROOF | INVALID_VEHICLE_PROOF | Yes | Lab | PASS |
| VT-006 | Replay | REPLAY_DETECTED | REPLAY_DETECTED | Yes | Yes | PASS |
| VT-007 | Expired challenge | EXPIRED_CHALLENGE | EXPIRED_CHALLENGE | Yes | Lab | PASS |
| VT-008 | Revoked credential | CREDENTIAL_REVOKED | CREDENTIAL_REVOKED | Yes | Lab | PASS |
| VT-009 | Authorized rebinding | VERIFIED | VERIFIED | Yes | Yes | PASS |
| VT-010 | Unknown vehicle | UNKNOWN_VEHICLE | UNKNOWN_VEHICLE | Yes | API | PASS |
| VT-011 | Malformed credential | CONTROLLED_REJECTION | TAMPERED_CREDENTIAL | Yes | API | PASS |
| VT-012 | Secure module offline | SECURE_MODULE_UNAVAILABLE | SECURE_MODULE_UNAVAILABLE | Yes | Lab | PASS |
| LC-001–010 | Lifecycle suite | Required exact outcomes | Required exact outcomes | Yes | Lifecycle/full demo | PASS |
