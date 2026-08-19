from concurrent.futures import ThreadPoolExecutor

from vehicletrust.models import Credential, PlateVehicleBinding, Vehicle
from vehicletrust.services import ControlledSecurityError, authorized_rebind


def test_concurrent_rebinding_allows_exactly_one_winner(app):
    def attempt(destination: str) -> str:
        with app.app_context():
            credential = Credential.query.filter_by(vehicle_trust_id="VT-7A82F1").one()
            vehicle = Vehicle.query.filter_by(vehicle_trust_id=destination).one()
            try:
                authorized_rebind(
                    credential,
                    vehicle,
                    reason="Concurrent integrity test",
                    authorization_reference=f"THREAD-{destination}",
                )
                return "SUCCESS"
            except ControlledSecurityError:
                return "DENIED"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, ["VT-91B4D7", "VT-C3D8E2"]))
    assert sorted(outcomes) == ["DENIED", "SUCCESS"]
    with app.app_context():
        assert PlateVehicleBinding.query.filter_by(status="ACTIVE").count() >= 1
