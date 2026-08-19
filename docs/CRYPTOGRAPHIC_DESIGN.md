# Cryptographic Design

## Physical-plate credential

The visual credential uses canonical CBOR and COSE_Sign1 semantics with ES256 (ECDSA P-256/SHA-256). Integer-keyed protected data contains only protocol version, an 8-byte credential reference, and a 6-byte Plate UID reference. The COSE envelope carries issuer key ID `VTO1` and a fixed-width 64-byte ES256 signature. Full mutable data remains in the registry.

The QR contains the raw 101-byte COSE value. API/lab transport uses `VT1:` plus Base45. The generated image is decoded and signature-verified in automated tests; a changed protected byte fails issuer verification.

## Live vehicle proof

The challenge includes a 256-bit OS-CSPRNG nonce, unique challenge ID, credential ID, dynamically resolved expected VehicleTrust ID, timestamp, and expiry. The responding module signs canonical challenge bytes. The backend verifies with the registered responder public key, checks expiry/one-time state, consumes the challenge, compares responder to the active binding, and evaluates registry status.

## Key boundaries

Issuer and simulated vehicle private PEM files live only in the ignored Flask instance directory. SQLite stores public keys, fingerprints, and opaque secure-key references. Templates, APIs, code images, logs, screenshots, documentation, and repository checks expose no private key. The software boundary demonstrates the interface but is not equivalent to a certified secure element or HSM.

## Validity distinction

Cryptographic validity is immutable evidence that the issued Plate UID was not changed. Operational validity is current authorization/status: active, reserved, lost, stolen, retired, replaced, revoked, or bound. A mathematically valid old credential can therefore be denied as `RETIRED_PHYSICAL_PLATE`, `LOST_PLATE`, or another registry decision.
