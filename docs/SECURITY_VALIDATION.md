# Security Validation

## Automated validation

The test suite executes issuer negative cases, independent vehicle keys, QR image decode and signature
round trip, complete verification, every attack decision, challenge consumption, deterministic expiry,
rebind history, malformed inputs, administrator separation, failure injection and security invariants.

Latest recorded automated run:

```text
SECURITY VALIDATION REPORT

[PASS] Normal Vehicle Verification
[PASS] QR Clone Detection
[PASS] Physical Plate Transfer Detection
[PASS] Credential Tamper Detection
[PASS] Replay Attack Detection
[PASS] Expired Challenge Detection
[PASS] Credential Revocation
[PASS] Authorized Plate Rebinding

62 collected · 62 passed · 0 failed · 0 skipped
```

Browser flows passed for normal verification, genuine plate swap, replay and authorized rebinding.
Responsive overflow checks passed at 1440×900, 1280×720 and 390×844. Running-application evidence is
recorded in `SECURITY_TEST_MATRIX.md`, `FINAL_BUILD_REPORT.md` and `docs/screenshots/`.
