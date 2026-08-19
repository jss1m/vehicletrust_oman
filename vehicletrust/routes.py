import json
import secrets
from functools import wraps

from flask import Blueprint, abort, current_app, jsonify, render_template, request
from sqlalchemy import text

from .extensions import db
from .models import (
    AuditEvent,
    Challenge,
    Credential,
    Owner,
    PlateEntitlement,
    PlateVehicleBinding,
    Vehicle,
    VehicleOwnership,
)
from .services import (
    ControlledSecurityError,
    active_credential,
    authorized_rebind,
    credential_content,
    issue_credential,
    reset_demo,
    revoke_credential,
    run_full_demo,
    run_lifecycle_scenario,
    run_scenario,
    seed_demo,
    verify_vehicle,
)

bp = Blueprint("main", __name__)


def demo_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = request.headers.get("X-Demo-Admin-Token") or request.form.get("demo_admin_token")
        configured = current_app.config.get("DEMO_ADMIN_TOKEN")
        if not configured or not token or not secrets.compare_digest(token, configured):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Demo administrator authorization required"}), 403
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@bp.app_context_processor
def inject_globals():
    return {"demo_mode": current_app.config["DEMO_MODE"]}


def demo_write_allowed() -> bool:
    if current_app.config["DEMO_MODE"]:
        return True
    token = request.headers.get("X-Demo-Admin-Token") or request.form.get("demo_admin_token", "")
    configured = current_app.config.get("DEMO_ADMIN_TOKEN") or ""
    return bool(token and configured and secrets.compare_digest(token, configured))


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "application": "VehicleTrust Oman"})


@bp.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "service": "VehicleTrust Oman"})


@bp.get("/readyz")
def readyz():
    try:
        db.session.execute(text("SELECT 1"))
        seed_demo()
        ready = Vehicle.query.count() >= 2 and Credential.query.count() >= 2
    except Exception:
        current_app.logger.exception("Readiness dependency check failed")
        ready = False
    status = 200 if ready else 503
    return (
        jsonify({"status": "ready" if ready else "not_ready", "service": "VehicleTrust Oman"}),
        status,
    )


@bp.get("/")
def landing():
    seed_demo()
    return render_template("landing.html")


@bp.get("/dashboard")
def dashboard():
    seed_demo()
    events = AuditEvent.query.order_by(AuditEvent.id.desc()).limit(8).all()
    stats = {
        "vehicles": Vehicle.query.count(),
        "credentials": Credential.query.filter_by(status="ACTIVE").count(),
        "attempts": AuditEvent.query.filter_by(event_type="VEHICLE_VERIFICATION").count(),
        "verified": AuditEvent.query.filter_by(result="VERIFIED").count(),
        "alerts": AuditEvent.query.filter(
            AuditEvent.risk_level.in_(["WARNING", "CRITICAL"])
        ).count(),
        "replays": AuditEvent.query.filter_by(result="REPLAY_DETECTED").count(),
        "revoked": Credential.query.filter(
            Credential.status.in_(["REVOKED", "SUPERSEDED"])
        ).count(),
    }
    return render_template("dashboard.html", stats=stats, events=events)


@bp.get("/vehicles")
@bp.get("/registry")
def registry():
    seed_demo()
    vehicles = Vehicle.query.order_by(Vehicle.id).all()
    rows = []
    for vehicle in vehicles:
        credential = active_credential(vehicle.vehicle_trust_id)
        last = (
            AuditEvent.query.filter_by(expected_vehicle=vehicle.vehicle_trust_id)
            .order_by(AuditEvent.id.desc())
            .first()
        )
        rows.append((vehicle, credential, last))
    return render_template("registry.html", rows=rows)


@bp.get("/vehicles/<vehicle_trust_id>")
def vehicle_detail(vehicle_trust_id):
    vehicle = Vehicle.query.filter_by(vehicle_trust_id=vehicle_trust_id).first_or_404()
    credential = (
        Credential.query.filter_by(vehicle_trust_id=vehicle_trust_id)
        .order_by(Credential.id.desc())
        .first()
    )
    last_challenge = (
        Challenge.query.filter_by(expected_vehicle_id=vehicle_trust_id)
        .order_by(Challenge.id.desc())
        .first()
    )
    events = (
        AuditEvent.query.filter(
            db.or_(
                AuditEvent.expected_vehicle == vehicle_trust_id,
                AuditEvent.responding_vehicle == vehicle_trust_id,
            )
        )
        .order_by(AuditEvent.id.desc())
        .limit(10)
        .all()
    )
    verification_events = [event for event in events if event.event_type == "VEHICLE_VERIFICATION"]
    last_authentication = next(
        (event for event in verification_events if event.result == "VERIFIED"), None
    )
    return render_template(
        "vehicle_detail.html",
        vehicle=vehicle,
        credential=credential,
        last_challenge=last_challenge,
        events=events,
        last_authentication=last_authentication,
        failed_verifications=sum(event.result != "VERIFIED" for event in verification_events),
        replay_attempts=sum(event.result == "REPLAY_DETECTED" for event in verification_events),
    )


@bp.route("/credentials/issue", methods=["GET", "POST"])
def credential_issue():
    seed_demo()
    vehicles = Vehicle.query.order_by(Vehicle.id).all()
    issued = None
    error = None
    if request.method == "POST":
        if not demo_write_allowed():
            abort(403)
        vehicle = Vehicle.query.filter_by(
            vehicle_trust_id=request.form.get("vehicle_id")
        ).first_or_404()
        try:
            issued = issue_credential(
                vehicle,
                plate_number=request.form.get("plate_number"),
                plate_code=request.form.get("plate_code", "").upper(),
            )
        except ControlledSecurityError as exc:
            error = str(exc)
    return render_template("credential_issue.html", vehicles=vehicles, issued=issued, error=error)


@bp.get("/credentials/<credential_id>/code")
def credential_code_detail(credential_id):
    credential = Credential.query.filter_by(credential_id=credential_id).first_or_404()
    return render_template("credential_code.html", credential=credential)


@bp.route("/verify", methods=["GET", "POST"])
def verify():
    seed_demo()
    vehicles = Vehicle.query.order_by(Vehicle.id).all()
    credentials = Credential.query.order_by(Credential.id.desc()).all()
    result = None
    selected_credential = None
    if request.method == "POST":
        selected_credential = Credential.query.filter_by(
            credential_id=request.form.get("credential_id")
        ).first_or_404()
        result = verify_vehicle(
            credential_content(selected_credential), request.form.get("responding_vehicle_id", "")
        )
    elif request.args.get("vehicle"):
        selected_credential = active_credential(request.args["vehicle"])
    return render_template(
        "verify.html",
        vehicles=vehicles,
        credentials=credentials,
        selected_credential=selected_credential,
        result=result,
    )


@bp.route("/security-lab", methods=["GET", "POST"])
def security_lab():
    result = None
    if request.method == "POST":
        scenario = request.form.get("scenario", "")
        try:
            result = run_scenario(scenario)
        except ControlledSecurityError as exc:
            result = {
                "passed": False,
                "expected": "CONTROLLED_RESULT",
                "actual": "ERROR",
                "details": {"reason": str(exc), "steps": []},
            }
    return render_template("security_lab.html", result=result)


@bp.post("/security-lab/full-demo")
def full_demo():
    result = run_full_demo()
    return render_template("full_demo.html", demo=result)


@bp.get("/audit")
def audit_trail():
    events = AuditEvent.query.order_by(AuditEvent.id.desc()).limit(250).all()
    return render_template("audit.html", events=events, json=json)


@bp.get("/architecture")
def architecture():
    return render_template("architecture.html")


@bp.get("/security-design")
def security_design():
    return render_template("security_design.html")


@bp.route("/lifecycle", methods=["GET", "POST"])
def lifecycle():
    seed_demo()
    result = None
    if request.method == "POST":
        try:
            result = run_lifecycle_scenario(request.form.get("scenario", ""))
        except ControlledSecurityError as exc:
            result = {"passed": False, "expected": "CONTROLLED_RESULT", "actual": str(exc)}
    portfolios = []
    for owner in Owner.query.order_by(Owner.id).all():
        portfolios.append(
            {
                "owner": owner,
                "vehicles": VehicleOwnership.query.filter_by(
                    owner_id=owner.id, status="ACTIVE"
                ).count(),
                "plates": PlateVehicleBinding.query.join(
                    VehicleOwnership,
                    PlateVehicleBinding.vehicle_id == VehicleOwnership.vehicle_id,
                )
                .filter(
                    VehicleOwnership.owner_id == owner.id,
                    VehicleOwnership.status == "ACTIVE",
                    PlateVehicleBinding.status == "ACTIVE",
                )
                .count(),
                "reserved": PlateEntitlement.query.filter_by(
                    owner_id=owner.id, status="RESERVED"
                ).count(),
            }
        )
    return render_template("lifecycle.html", result=result, portfolios=portfolios)


@bp.route("/rebind", methods=["GET", "POST"])
def rebind():
    seed_demo()
    vehicles = Vehicle.query.order_by(Vehicle.id).all()
    credentials = Credential.query.order_by(Credential.id.desc()).all()
    result = None
    error = None
    if request.method == "POST":
        if not demo_write_allowed():
            abort(403)
        credential = Credential.query.filter_by(
            credential_id=request.form.get("credential_id")
        ).first_or_404()
        vehicle = Vehicle.query.filter_by(
            vehicle_trust_id=request.form.get("new_vehicle_id")
        ).first_or_404()
        try:
            result = authorized_rebind(
                credential,
                vehicle,
                reason=request.form.get("reason") or "Authorized transfer",
                authorization_reference=request.form.get("authorization_reference")
                or "DEMO-REFERENCE",
                operator=request.form.get("operator") or "Demo Admin",
            )
        except ControlledSecurityError as exc:
            error = str(exc)
    return render_template(
        "rebind.html", vehicles=vehicles, credentials=credentials, result=result, error=error
    )


@bp.post("/api/lab/<scenario>")
def api_lab_scenario(scenario):
    try:
        return jsonify(run_scenario(scenario))
    except ControlledSecurityError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/api/lab/full-demo")
def api_full_demo():
    return jsonify(run_full_demo())


@bp.post("/api/admin/reset")
@demo_admin_required
def api_reset():
    reset_demo()
    return jsonify({"status": "reset", "vehicles": Vehicle.query.count()})


@bp.post("/api/admin/credentials/<credential_id>/revoke")
@demo_admin_required
def api_revoke(credential_id):
    credential = Credential.query.filter_by(credential_id=credential_id).first_or_404()
    revoke_credential(credential)
    return jsonify({"result": "CREDENTIAL_REVOKED", "credential_id": credential_id})


@bp.errorhandler(400)
@bp.errorhandler(403)
@bp.errorhandler(404)
@bp.errorhandler(413)
def controlled_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": error.name, "message": error.description}), error.code
    return render_template("error.html", error=error), error.code
