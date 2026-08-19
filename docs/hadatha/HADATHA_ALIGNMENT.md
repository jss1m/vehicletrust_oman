# Hadatha Alignment

Source of truth: [Hadatha Excellence Initiative in Cybersecurity Industry](https://cert.gov.om/sp/HadathaAwards). The official page emphasizes cybersecurity innovation, originality, expected social/economic value, demonstrated results, and supporting evidence. This prototype is prepared as supporting material; it does not claim selection, approval, or government deployment.

## Cybersecurity Problem

A mathematically authentic plate credential can be cloned or physically moved. Artifact authenticity alone does not authenticate the vehicle carrying it.

## Proposed Innovation

VehicleTrust separates physical Plate UID, plate-number entitlement, ownership, live vehicle identity, active binding, and operational status. It combines a static signed plate credential with fresh vehicle-held-key proof and an auditable registry decision.

## Why This Is Cybersecurity

The design addresses identity spoofing, credential cloning/tampering, replay, unauthorized binding, revoked/lost physical identities, key isolation, and fail-closed dependency behavior.

## Threat Model

Adversaries may copy a code, move a genuine plate, alter protected bytes, replay old proof, claim another vehicle identity, or reuse a retired/lost plate. Controls include ES256 signatures, isolated per-vehicle keys, nonces, expiry, one-time challenges, registry status, partial unique constraints, transactions, and audit evidence.

## Technical Differentiation

The innovation is not QR. The code is a compact carrier for immutable physical identity. Security comes from independently proving issuer authenticity, current registry authorization, fresh vehicle identity, binding, and operational status.

## Expected Social Impact

If validated through future pilots, the approach could make selected plate-transfer and identity-reuse patterns easier to detect and provide clearer evidence for fleet, rental, inspection, and investigation workflows. No reduction percentage is claimed.

## Expected Economic Impact

Potential value includes reusable identity-assurance components, better fleet/rental asset controls, and local cybersecurity engineering capability. Financial outcomes require field evidence and are not estimated here.

## Target Users

Future controlled pilots could involve private fleets, rental operators, inspection environments, OEM/security researchers, and—only through formal future engagement—relevant public authorities.

## Prototype Results

Executed automated and browser tests demonstrate compact-code round trip, tamper rejection, genuine-plate swap detection, cloning, impersonation, replay, expiry, revocation, secure-module failure, static-code rebinding, ownership/entitlement lifecycle, retired/lost/reserved status, stolen-vehicle alerting, rollback, and concurrent-binding protection.

## Current Limitations

Software-only simulated secure modules; synthetic registry; no vehicle bus, reader hardware, government data, ROP integration, hardware certification, external identity proofing, production RBAC, or field pilot.

## Future Development

Software MVP → secure-element hardware prototype → private-fleet pilot → controlled field pilot → OEM/government integration research.

## Supporting Evidence Index

Validation matrices, threat model, cryptographic design, test suite, browser tests, real screenshots, feasibility, limitations, demo script, CI workflow, deployment blueprint, dependency/security checks, and final build report.
