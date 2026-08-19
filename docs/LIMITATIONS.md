# Limitations

- The vehicle secure element is simulated with a local software module.
- No real vehicle, roadside reader or hardware bus is connected.
- No Royal Oman Police integration, logo, data, approval or endorsement exists.
- All plates and vehicle records are synthetic and visibly marked as prototypes.
- Computer vision and plate recognition are optional and simulated.
- Local Demo Admin controls are not production authentication or RBAC.
- Local file-backed keys do not provide HSM-grade extraction resistance, attestation or lifecycle control.
- SQLite and the Flask development server are suitable for a local MVP, not resilient deployment.
- Production deployment requires certified hardware, secure provisioning, reader authentication,
  anti-relay design, privacy and legal review, government authorization, audited administration,
  scalable infrastructure and independent penetration testing.

