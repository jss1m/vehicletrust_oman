# FINAL BUILD REPORT

## Status

**Final repository cleanup completed. Strict final gate: NOT READY pending one successful Gunicorn
smoke run on Linux/Ubuntu CI.** The application, automated tests, security regression, lifecycle
regression, WSGI routes, Ruff, and repository checks pass. This is not a production, certified,
government-connected, or field-validated system.

## Final Repository Validation — 2026-08-19

### Automated Tests

- Baseline collected: 62
- Baseline passed: 62
- Baseline failed: 0
- Baseline skipped: 0
- Post-cleanup collected: 62
- Post-cleanup passed: 62
- Post-cleanup failed: 0
- Post-cleanup skipped: 0
- Final command: `pytest -v`
- Final duration in the intended repository `D:\GitHub\vehicletrust_oman`: 183.60s

### Ruff

PASS.

### Repository Check

PASS — `REPOSITORY READY`; required release files, CI, Hadatha evidence, 23 screenshots,
local image links/path casing, tracked-secret exclusions, and obvious secret patterns validated.

### Gunicorn

NOT COMPLETED. The exact command was attempted on Windows and stopped before application startup
because Gunicorn requires the Unix-only `fcntl` module. No WSL distribution or Docker runtime is
available on this host. `.github/workflows/ci.yml` now contains the exact one-worker Gunicorn command
and HTTP checks for all required routes on Ubuntu, but that remote workflow has not been executed from
this uncommitted working tree. The same `wsgi:app` was loaded locally and all required routes returned
HTTP 200.

### Security Regression

PASS — all 10 required security acceptance scenarios returned their exact expected decisions.

### Lifecycle Regression

PASS — all 10 lifecycle acceptance scenarios passed, including duplicate-binding prevention,
rollback, replacement, loss, ownership/entitlement flows, and exactly one concurrent rebind winner.

### GitHub CI

- Workflow file: PRESENT at `.github/workflows/ci.yml`.
- Configuration review: PASS for `push` and `pull_request` to `main`, Python 3.12, dependency and
  Chromium installation, pytest, Ruff, repository readiness, and Linux Gunicorn route smoke test.
- Actual GitHub Actions run for this working tree: NOT RUN.

### Deployment

- Render configuration: READY — repository-root paths, one worker, four threads, health probe,
  generated secrets, no mandatory paid persistent disk.
- Public site: NOT REQUIRED / NOT DEPLOYED.
- Deployment-ready; no public live deployment required for the current submission.

### Hadatha Evidence

- README: PASS.
- Hadatha docs: PASS.
- Screenshots: PASS — 23 present and non-empty.
- Security Test Matrix: PASS.

## Application

- Local WSGI application load: PASS.
- Required routes: PASS — `/`, `/healthz`, `/readyz`, `/registry`, `/verify`, `/security-lab`,
  `/lifecycle`, `/audit`, and `/architecture` returned HTTP 200.
- Empty database initialization and synthetic seed: PASS.
- Restart and persistence: PASS; a second process reopened the same database and returned `VERIFIED` for the persisted active binding.

## Fresh Build

NOT RUN during this cleanup. Validation used the existing Python 3.12.13 virtual environment. A prior
clean-environment result is intentionally not reported as a current PASS.

## Credential Code

- Format: compact standard QR; canonical CBOR in COSE_Sign1 semantics; ES256/P-256; issuer key ID `VTO1`.
- Payload fields: version, 8-byte credential reference, 6-byte immutable Plate UID reference.
- Encoded visual value: 101 bytes raw COSE.
- Text/API transport: `VT1:` Base45, under 200 bytes.
- Rendered size: QR version 5, ECC-L, mask 4, four-module quiet zone, 112×112 CSS pixels in a 140px plate body (80-signature comparison plus fresh-suite samples).
- Decode test: PASS from the generated PNG through OpenCV.
- Signature round trip: PASS.
- Corrupted image/protected data: controlled rejection PASS.
- Data Matrix decision: rejected because its available generation/decoding path added fragile deployment dependencies.

## Tests

- Collected: 62
- Passed: 62
- Failed: 0
- Skipped: 0
- Pre-cleanup validation on an identical `origin/main` checkout: 62 passed in 153.21s.
- Post-cleanup `pytest -v` in `D:\GitHub\vehicletrust_oman`: 62 passed in 183.60s.
- Ruff check: PASS.
- Ruff format check: PASS (50 files).
- Bandit: PASS (optional local check).
- Repository readiness/secret/evidence check: PASS.
- `pip-audit`: NOT RUN in this cleanup and not a mandatory CI gate.

## Security

| Scenario | Required / actual | Result |
|---|---|---|
| Normal Authentication | VERIFIED | PASS |
| Plate Swap | GENUINE_PLATE_WRONG_VEHICLE | PASS |
| Credential Clone | VEHICLE_IDENTITY_MISMATCH | PASS |
| Tampering | INVALID_DIGITAL_SIGNATURE | PASS |
| Vehicle Impersonation | INVALID_VEHICLE_PROOF | PASS |
| Replay | REPLAY_DETECTED | PASS |
| Expiry | EXPIRED_CHALLENGE | PASS |
| Revocation | CREDENTIAL_REVOKED | PASS |
| Authorized Rebinding | VERIFIED | PASS |
| Secure Module Failure | SECURE_MODULE_UNAVAILABLE | PASS |
| Stolen Vehicle Status | VERIFIED_IDENTITY_STOLEN_VEHICLE | PASS |

The combined 21-scenario deterministic Security/Lifecycle demo passed and completed in 7.38s in a measured CLI run.

## Identity Lifecycle

| Capability | Actual | Result |
|---|---|---|
| Static Plate UID / code across ordinary rebind | REBIND_SUCCESS_STATIC_CODE | PASS |
| Ownership transfer with binding unchanged | OWNERSHIP_CHANGED_BINDING_REMAINS | PASS |
| Sell vehicle and keep plate | RESERVED_PLATE | PASS |
| Reserved plate illegal use | not VERIFIED | PASS |
| Plate-number sale | old Plate UID retired, new issued and verified | PASS |
| Lost plate | old code LOST_PLATE, replacement verified | PASS |
| Damaged replacement | old REVOKED_PLATE, replacement verified | PASS |
| Multiple vehicles per owner | independent active bindings | PASS |
| Duplicate active binding | database constraint BLOCKED | PASS |
| Concurrent rebinding | exactly one of two threads succeeded | PASS |
| Transaction rollback | injected failure restored original binding | PASS |
| Audit history | superseded/closed rows and structured transaction evidence preserved | PASS |

## Database Migration Summary

The fresh schema adds `Owner`, `PlateNumber`, `PhysicalPlate`, `PlateEntitlement`, `VehicleOwnership`, and append-only `PlateVehicleBinding`; adds `Vehicle.theft_status`; and enriches `AuditEvent` with actor, Plate UID, previous/new vehicle and owner, and transaction ID. SQLite partial unique indexes enforce one active binding per PhysicalPlate, one active entitlement per plate number, and one active ownership record per vehicle. This prototype rebuilds the demo database from zero; a production rollout still needs Alembic migrations and backup/rollback planning.

## UI

- Desktop 1440×900: PASS.
- Desktop 1280×720: PASS.
- Mobile 390×844: PASS.
- Horizontal overflow: none on landing, dashboard, registry, detail/plate, verify, Security Lab, Lifecycle, Audit, and Architecture.
- Arabic `عُمان` RTL rendering: PASS.
- Browser console: no errors in the tested routes.
- Real UI flows: normal verification, swap, replay, authorized rebinding, full security/lifecycle demo PASS.

## Public Deployment

**Deployment-ready; no public live deployment required for the current submission.**

- URL: none supplied.
- Homepage/health/routes/assets/HTTPS: NOT RUN against a public host.
- Local startup/routes/assets: PASS.
- Live checker correctly refused to claim success without `PUBLIC_DEMO_URL`.

## GitHub

- Repository structure: PASS.
- Secrets check: PASS; no tracked `.env`, `.db`, `.pem`, or obvious embedded private key/secret values found by the readiness check.
- README: top-level problem, innovation, MVP evidence, verified test count, key screenshot, and
  evidence links updated.
- CI: `.github/workflows/ci.yml` is present and configured for pytest, Ruff, repository readiness,
  and a Linux Gunicorn route smoke test. It has not yet run for the local uncommitted changes.
- Deployment files: `wsgi.py`, `Procfile`, `render.yaml`, `.env.example`, `/healthz`, `/readyz`, live checker.

## Hadatha Evidence

- Screenshots: 23 real running-application PNGs, PASS.
- Security and lifecycle matrices: PASS.
- Arabic form draft: PASS.
- Feasibility and impact: PASS, with no fabricated figures.
- Demo script: PASS.
- Official-alignment document and supporting-evidence index: PASS.

## Known Limitations

- Simulated file-backed vehicle secure modules and demo issuer; no certified hardware/HSM.
- Synthetic registry and plates; no vehicle, reader, ROP, government data, approval, or integration.
- SQLite and in-process concurrency lock are not a distributed production design.
- Demo Admin mode is not production authentication/RBAC.
- No relay-resistance proof, CAN-theft prevention, towing/GPS-jamming control, or defense after genuine key/hardware compromise.
- No field pilot, impact percentage, financial result, legal/governance approval, privacy assessment, hardware certification, or independent penetration test.
- QR reliability required 112px, above the desired 60–72px target; earlier 88px and 100px estimates were rejected after randomized test failures.
- External dependency vulnerability audit remained incomplete because the service timed out.
- Gunicorn cannot start natively on this Windows host; the required Linux CI smoke test remains to be
  executed after commit/push.

## How to Run

```powershell
cd vehicletrust_oman
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe run.py
```

Open `http://127.0.0.1:5000`, then use **Security Lab → Run Full Security Demo** and **Lifecycle**.
