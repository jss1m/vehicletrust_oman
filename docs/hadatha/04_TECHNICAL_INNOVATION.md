# Technical Innovation

The innovation is not QR/Data Matrix. The security value comes from multi-factor identity assurance and fresh plate-to-vehicle cryptographic proof:

1. A canonical CBOR/COSE_Sign1 credential authenticates immutable physical Plate UID.
2. An auditable registry resolves entitlement, current binding, status, and history.
3. A fresh nonce is signed by the responding vehicle's independent P-256 key.
4. The decision engine separates identity confirmation from operational state, such as a reported-stolen vehicle.
5. Authorized rebinding changes the registry relationship without rewriting the static plate code; physical loss or ownership transfer retires it and issues a new Plate UID.
