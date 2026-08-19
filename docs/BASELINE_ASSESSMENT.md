# Baseline Assessment

Assessment date: 2026-08-19. Baseline command: `pytest -q` — 39 passed; Ruff passed.

## What already worked

The existing Flask/SQLAlchemy MVP had two synthetic vehicles, issuer and vehicle P-256 keys, signed credentials, one-time challenge/response, replay and expiry checks, revocation, rebinding, audit events, a working Security Lab, browser tests, and twelve real application screenshots.

## What was broken or incomplete

- The visual code transported a 511-byte verbose JSON document and dominated the plate.
- The code represented the then-current vehicle association instead of an independent physical plate identity.
- Rebinding revoked the old credential and issued a different code; it did not model static Plate UID plus dynamic registry binding.
- Owner, entitlement, ownership history, physical-plate status, vehicle theft status, lifecycle transaction, and concurrency models were absent.
- Impersonation and secure-module-offline were not judge-facing scenarios.
- There was no `/healthz`, `/readyz`, production WSGI entry point, Render blueprint, CI workflow, dependency audit, or repository readiness check.

## Security weaknesses

The old demo admin token could be rendered into forms, the default development secret was predictable, sensitive lifecycle changes lacked a complete domain model, and a multi-step rebind committed in stages. Production RBAC, HSM/secure-element storage, migration tooling, rate limiting, and external registry availability remain future requirements.

## UX problems

The code was visually oversized, the Lab omitted attack/control labels and several outcomes, and cryptographic validity was not clearly separated from operational authorization.

## Missing tests

Actual image decode/corruption, measured visual size, impersonation, offline fail-closed behavior, static Plate UID, entitlement/ownership lifecycle, retired/lost/reserved status, transaction rollback, and concurrent rebinding were missing.

## Required changes

Adopt canonical CBOR/COSE_Sign1, keep full mutable data in the registry, add lifecycle entities and invariants, preserve historical rows, make rebinding atomic, expand attack/lifecycle demos, harden configuration, add release automation, and regenerate evidence only after real flows pass.
