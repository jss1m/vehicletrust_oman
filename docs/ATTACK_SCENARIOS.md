# Attack Scenarios

## Normal verification

Plate A and Vehicle A pass issuer signature, active status, fresh challenge, vehicle proof and binding.
Expected result: `VERIFIED`.

## Genuine physical plate swap

The complete authentic Plate A is presented while Vehicle B responds. Credential signature remains
valid and Vehicle B produces a valid proof for B. The expected identity is A, so binding fails.
Expected result: `GENUINE_PLATE_WRONG_VEHICLE`.

## Exact QR clone

An unchanged copy of QR A is attached to Vehicle B. QR authenticity passes; binding fails.
Expected result: `VEHICLE_IDENTITY_MISMATCH`.

## Credential tampering

One protected VehicleTrust ID field is changed without resigning. Signature validation fails and the
system does not create a challenge. Expected result: `INVALID_DIGITAL_SIGNATURE`.

## Replay

A successful response and its exact challenge are resubmitted. Persisted `used_at` prevents a second
acceptance. Expected result: `REPLAY_DETECTED`.

## Expiry and revocation

Expired challenges are rejected before signature acceptance. Revoked credentials are denied even when
their issuer signature remains correct.

## Authorized rebinding

The old binding is ended, the old credential is superseded, authorization evidence is stored and a new
credential for Vehicle B is issued. New Plate A + Vehicle B verifies; the old credential and Vehicle A
with the new credential remain denied.
