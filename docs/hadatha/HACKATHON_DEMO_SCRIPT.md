# Hackathon Demo Script (4–5 minutes)

## 0:00–0:30 — Problem

Show the compact fictional plate. Explain: a valid signature proves the plate artifact, but a genuine plate can still be on the wrong vehicle.

## 0:30–1:00 — Authentic identity

Run Plate A + Vehicle A. Point to issuer signature, registry lookup, fresh challenge, vehicle proof, binding, and `VERIFIED`.

## 1:00–1:45 — Genuine plate transfer

Run Plate A + Vehicle B. Emphasize that plate and vehicle-B proof are each valid, but their binding fails: `GENUINE PLATE — WRONG VEHICLE`.

## 1:45–2:15 — Replay and tamper

Run replay, then tamper. Show one-time challenge state and invalid issuer signature; challenge/response does not run after credential authentication failure.

## 2:15–3:00 — Legitimate lifecycle

Authorized rebind Plate A from A to B. Show that Plate UID/code stays unchanged, old binding becomes superseded, new binding becomes active, and B verifies.

## 3:00–3:40 — Sale/reissue and status

Sell the plate number: old Plate UID becomes retired, new physical identity is issued, old scan is denied, and the new plate verifies. Run reported-stolen vehicle: identity is confirmed but an operational alert is raised.

## 3:40–4:30 — Evidence and future

Show audit history, architecture, full demo, test matrix, and limitations. Future path: hardware secure element and controlled private-fleet pilot. State clearly that all data is synthetic and there is no ROP/government connection.
