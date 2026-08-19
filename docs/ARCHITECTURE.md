# Architecture

```text
Physical Plate
  ├─ visible Plate Number
  ├─ immutable Plate UID
  └─ signed compact code
             ↓
Identity Registry
  ├─ number entitlement
  ├─ active/historic binding
  ├─ ownership history
  └─ plate + vehicle status
             ↓
Expected Vehicle → Fresh Challenge → Vehicle Secure Module
                                      ↓ signed proof
Identity Assurance → Operational Status → Audit Evidence
```

The issuer answers “is this physical plate credential authentic?” The active registry binding answers “which vehicle is currently authorized?” The independent vehicle key answers “which vehicle is present now?” Freshness and one-time state prevent old proof reuse. Operational status then distinguishes an authenticated identity from an authorized, clear-status outcome.

## Domain separation

- `Owner`: synthetic person/entity reference.
- `VehicleOwnership`: append-only ownership history; not the identity binding.
- `PlateNumber`: visible registration number.
- `PlateEntitlement`: current right to hold/use the number.
- `PhysicalPlate`: immutable non-sequential Plate UID, credential, and operational state.
- `PlateVehicleBinding`: append-only current/historical physical-plate association.
- `Vehicle`: independent cryptographic identity and theft/registration/module status.
- `Credential`: signed compact physical-plate reference.

SQLite partial unique indexes enforce one active binding per physical plate, one active entitlement per plate number, and one active ownership record per vehicle. Lifecycle services use a transaction boundary and lock; production multi-instance deployment requires database-native row locking/serializable transactions.

`SimulatedVehicleSecureModule` can be replaced by a hardware adapter while retaining only signing, public-identity, and status operations. A production design additionally needs authenticated readers, anti-relay controls, attestation, secure provisioning, HSM issuer operations, RBAC, privacy governance, monitoring, and independent assessment.
