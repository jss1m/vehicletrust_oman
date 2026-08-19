# Limitations

- Synthetic vehicles, owners, VINs, plates, registry, and authority.
- Simulated file-backed vehicle secure modules; no real secure element.
- No connection to a vehicle, CAN bus, inspection reader, ROP, or government data.
- No claim to prevent theft, towing, relay, jamming, key compromise, or hardware attacks.
- SQLite and in-process locking suit the demo, not distributed production concurrency.
- Demo-admin mode is not production authentication/RBAC.
- No migration framework, external availability design, HSM, key ceremony, certification, privacy impact assessment, or field-pilot results.
- QR was selected for deployment reliability; the measured 112px size exceeded the desired 60–72px target.
