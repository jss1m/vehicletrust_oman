# Compact Credential Code Decision

## Evaluated formats

Data Matrix ECC200 was considered first. Reliable Python generation and decoding would have introduced native/runtime dependencies not already available in the deployment path. Compact standard QR is supported by the pure-Python `qrcode` production dependency and OpenCV in tests, so it was selected for repeatable local, CI, deployment, and screenshot behavior.

## Encoding

- Logical fields: protocol version, 8-byte credential reference, 6-byte immutable Plate UID reference.
- Serialization: canonical CBOR.
- Signature envelope: COSE_Sign1 semantics, ES256, issuer key ID `VTO1`.
- Visual transport: raw 101-byte COSE value; text/API transport: `VT1:` plus Base45.
- Full vehicle, ownership, entitlement, plate number, VIN, make/model/color, and all private keys remain outside the code.

## Render and decode evidence

The raw payload produces QR version 5 with ECC-L, a four-module quiet zone, and deterministic mask pattern 4. Automated tests start at 60 CSS pixels and increase by 4. An 80-signature mask comparison reached 108px for the selected mask, while a later fresh-suite sample reached 112px. The plate therefore renders the image at 112×112 CSS pixels inside a 140px plate body and offers a click-to-zoom detail page. Reliability was chosen over the original 60–72 px visual target; earlier 88px and 100px estimates were rejected after randomized failures.

The automated round trip is: issue → sign → CBOR/COSE → QR PNG → OpenCV decode → reconstruct → verify issuer signature. Corrupted image data and a modified protected field are both rejected without reaching vehicle challenge/response.
