# Feasibility

## Current software MVP

Flask, SQLAlchemy, SQLite, P-256 cryptography, compact CBOR/COSE, QR, local SVG assets, Playwright, and pytest produce a reproducible demonstration on a standard laptop.

## Future secure element

`VehicleSecureModule` exposes signing, public identity, and status—not raw private key retrieval—so a hardware adapter can replace the simulated module.

## Potential pilot

A private fleet pilot could use managed readers, provisioned hardware keys, a controlled registry, operator RBAC, and incident procedures before any public-road research.

## Infrastructure and limitations

Production work requires managed database/high availability, HSM-backed issuer key, hardware attestation/certification, authenticated administration, monitoring, privacy assessment, reader anti-tamper controls, recovery policy, and legal/governance agreements.
