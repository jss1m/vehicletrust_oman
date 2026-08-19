# Hackathon Demo

## Four-minute flow

1. **0:00–0:30:** Two identical-looking white Land Cruisers make visual attributes insufficient.
2. **0:30–1:00:** Plate A + Vehicle A produces `VERIFIED` after a fresh proof.
3. **1:00–2:00:** Move authentic Plate A to Vehicle B. Signature and B's proof pass; binding fails with
   `GENUINE PLATE — WRONG VEHICLE`.
4. **2:00–2:30:** Copy QR A exactly to B. It remains authentic but returns identity mismatch.
5. **2:30–3:00:** Replay the prior valid response. The used challenge is rejected.
6. **3:00–3:30:** Run authorized rebinding. Historic evidence remains; a new Plate A credential for B
   verifies.
7. **3:30–4:00:** Show issuer, registry and vehicle-key roots of trust and the secure-element adapter.

## Recovery

Use **Run Full Demo** at any time. It resets the synthetic database into a deterministic state before
executing all scenarios, so the committee flow does not depend on prior clicks.

