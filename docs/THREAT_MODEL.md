# Threat Model

## Assets and trust boundaries

Protected assets are issuer signing authority, vehicle private keys, active plate-to-vehicle bindings,
challenge freshness state and audit evidence. The QR and physical plate are treated as observable and
copyable. The network between reader, service and vehicle is simulated and therefore not trusted as a
production transport.

## Threats and controls

| Threat | Control | Safe decision |
|---|---|---|
| QR cloning | Live vehicle proof plus binding check | Vehicle identity mismatch |
| Genuine plate transfer | Vehicle proof remains valid for the responder; registry binding fails | Genuine plate, wrong vehicle |
| Protected-field tampering | Issuer ECDSA signature | Invalid plate signature; no challenge |
| Response replay | Unique one-time challenge ID and `used_at` | Replay detected |
| Delayed response | Challenge expiry | Expired challenge |
| Vehicle impersonation | Independent non-exported vehicle key | Invalid vehicle signature or mismatch |
| Revoked credential | Operational status checked after valid signature | Credential revoked |
| Unknown identity | Registry authorization distinct from cryptographic validity | Unknown vehicle |
| Dependency failure | Required checks fail closed | Fail closed |

## Explicitly out of scope

Relay resistance, physical tamper certification, camera-based plate reading, government identity
integration, production HSM operations, privacy impact assessment and fleet-scale availability are not
implemented in this software MVP.

