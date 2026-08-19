# Refactor Baseline

## Existing architecture and security flow

The project was a server-rendered Flask application with SQLAlchemy/SQLite, Jinja templates, local SVG assets, a demo issuer, simulated per-vehicle secure modules, signed plate credentials, registry lookup, fresh challenge/response, and audit logging.

## Existing tests

The pre-refactor suite contained 39 passing unit, integration, security, and Playwright tests. It covered issuance, issuer signatures, vehicle proof, clone/swap/tamper/replay/expiry/revocation/rebinding, audit output, malformed inputs, startup, and responsive pages.

## Problems found

`Credential.vehicle_trust_id` and a reissued QR made the visual credential track the current vehicle. The schema had no separate Owner, PlateNumber, PhysicalPlate, PlateEntitlement, VehicleOwnership, or append-only PlateVehicleBinding. Rebinding committed before issuance and therefore could leave partial state. Operational loss/theft/retirement and stolen-vehicle status were unmodelled.

## Required refactor

The refactor keeps the working Flask and cryptographic foundations but changes the trust lookup to: signed Plate UID → physical-plate status → active binding → expected vehicle → fresh proof → operational status. New partial unique indexes enforce one active binding per PhysicalPlate and one active entitlement/ownership record. Old bindings and ownership records are closed/superseded, never overwritten.
