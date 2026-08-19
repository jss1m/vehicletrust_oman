# VehicleTrust Validation Matrix

All rows below were executed by automated tests and/or the real Flask UI on 2026-08-19.

| Test | Expected | Actual | Automated | E2E | Status |
|---|---|---|---|---|---|
| VT-001 Normal | VERIFIED | VERIFIED | Yes | Yes | PASS |
| VT-002 Clone | VEHICLE_IDENTITY_MISMATCH | VEHICLE_IDENTITY_MISMATCH | Yes | Yes | PASS |
| VT-003 Plate Swap | GENUINE_PLATE_WRONG_VEHICLE | GENUINE_PLATE_WRONG_VEHICLE | Yes | Yes | PASS |
| VT-004 Tampering | INVALID_DIGITAL_SIGNATURE | INVALID_DIGITAL_SIGNATURE | Yes | Yes | PASS |
| VT-005 Impersonation | INVALID_VEHICLE_PROOF | INVALID_VEHICLE_PROOF | Yes | Lab UI | PASS |
| VT-006 Replay | REPLAY_DETECTED | REPLAY_DETECTED | Yes | Yes | PASS |
| VT-007 Expiry | EXPIRED_CHALLENGE | EXPIRED_CHALLENGE | Yes | Lab UI | PASS |
| VT-008 Revocation | CREDENTIAL_REVOKED | CREDENTIAL_REVOKED | Yes | Lab UI | PASS |
| VT-009 Secure Module Failure | SECURE_MODULE_UNAVAILABLE | SECURE_MODULE_UNAVAILABLE | Yes | Lab UI | PASS |
| LC-001 Keep Plate / New Vehicle | Static code + verified | REBIND_SUCCESS_STATIC_CODE | Yes | Lifecycle UI | PASS |
| LC-002 Sell Vehicle With Plate | Binding remains | OWNERSHIP_CHANGED_BINDING_REMAINS | Yes | Lifecycle UI | PASS |
| LC-003 Sell Vehicle / Keep Plate | RESERVED_PLATE | RESERVED_PLATE | Yes | Lifecycle UI | PASS |
| LC-004 Sell Plate Number | Old retired, new issued | OLD_PLATE_RETIRED_NEW_PLATE_ISSUED | Yes | Lifecycle UI | PASS |
| LC-005 Lost Plate | Old lost, replacement verified | OLD_PLATE_LOST_NEW_PLATE_ISSUED | Yes | Lifecycle UI | PASS |
| LC-006 Multiple Vehicles | Independent bindings | INDEPENDENT_ACTIVE_BINDINGS | Yes | Lifecycle UI | PASS |
| LC-007 Duplicate Binding | BLOCKED | BLOCKED | Yes | Lifecycle UI | PASS |
| LC-008 Stolen Vehicle | Confirmed identity + alert | VERIFIED_IDENTITY_STOLEN_VEHICLE | Yes | Lifecycle UI | PASS |
| LC-009 Plate Replacement | Old replaced, new issued | OLD_PLATE_REPLACED_NEW_PLATE_ISSUED | Yes | Lifecycle UI | PASS |
| LC-010 Concurrent Rebinding | One winner | ONE_TRANSACTION_ONLY | Two real threads | Lifecycle UI | PASS |
