"""Fresh-state security and lifecycle acceptance gate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vehicletrust import create_app
from vehicletrust.services import run_lifecycle_scenario, run_scenario


def require(label: str, actual: str, expected: str) -> None:
    status = "PASS" if actual == expected else "FAIL"
    print(f"[{status}] {label}: expected={expected} actual={actual}")
    if status == "FAIL":
        raise AssertionError(f"{label}: {actual} != {expected}")


def run() -> None:
    app = create_app()
    security = {
        "A Plate A + Vehicle A": ("normal", "VERIFIED"),
        "B Genuine Plate A + Vehicle B": ("swap", "GENUINE_PLATE_WRONG_VEHICLE"),
        "C Cloned credential + Vehicle B": ("clone", "VEHICLE_IDENTITY_MISMATCH"),
        "D Modified credential": ("tamper", "INVALID_DIGITAL_SIGNATURE"),
        "E Vehicle impersonation": ("impersonation", "INVALID_VEHICLE_PROOF"),
        "F Old response replay": ("replay", "REPLAY_DETECTED"),
        "G Expired challenge": ("expiry", "EXPIRED_CHALLENGE"),
        "H Revoked credential": ("revocation", "CREDENTIAL_REVOKED"),
        "I Secure module offline": ("offline", "SECURE_MODULE_UNAVAILABLE"),
        "J Authorized rebind A to B": ("rebinding", "VERIFIED"),
    }
    lifecycle = {
        "A Static Plate UID rebind": ("keep_plate", "REBIND_SUCCESS_STATIC_CODE"),
        "B Ownership sale, binding remains": (
            "sell_vehicle_with_plate",
            "OWNERSHIP_CHANGED_BINDING_REMAINS",
        ),
        "C Sell vehicle, keep plate": ("sell_vehicle_keep_plate", "RESERVED_PLATE"),
        "D Sell plate number": (
            "sell_plate_number",
            "OLD_PLATE_RETIRED_NEW_PLATE_ISSUED",
        ),
        "E Lost physical plate": ("lost_plate", "OLD_PLATE_LOST_NEW_PLATE_ISSUED"),
        "F Multiple owner vehicles": ("multiple_vehicles", "INDEPENDENT_ACTIVE_BINDINGS"),
        "G Duplicate active binding": ("duplicate_binding", "BLOCKED"),
        "H Stolen vehicle status": (
            "stolen_vehicle",
            "VERIFIED_IDENTITY_STOLEN_VEHICLE",
        ),
        "I Damaged plate replacement": (
            "plate_replacement",
            "OLD_PLATE_REPLACED_NEW_PLATE_ISSUED",
        ),
        "J Competing rebind": ("concurrent_rebinding", "ONE_TRANSACTION_ONLY"),
    }
    with app.app_context():
        for label, (scenario, expected) in security.items():
            require(label, run_scenario(scenario, reset=True)["actual"], expected)
        for label, (scenario, expected) in lifecycle.items():
            require(label, run_lifecycle_scenario(scenario, reset=True)["actual"], expected)
    print("FINAL SECURITY AND LIFECYCLE ACCEPTANCE: PASS")


if __name__ == "__main__":
    run()
