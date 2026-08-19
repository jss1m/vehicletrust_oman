from vehicletrust.models import PlateVehicleBinding
from vehicletrust.services import run_lifecycle_scenario


def test_binding_history_is_append_only(ctx):
    assert run_lifecycle_scenario("keep_plate")["passed"]
    bindings = PlateVehicleBinding.query.order_by(PlateVehicleBinding.id).all()
    assert any(item.status == "SUPERSEDED" and item.valid_until for item in bindings)
    assert any(item.status == "ACTIVE" for item in bindings)
