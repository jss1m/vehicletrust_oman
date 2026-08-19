from vehicletrust.services import run_lifecycle_scenario


def test_owner_can_hold_multiple_independent_vehicle_assets(ctx):
    assert run_lifecycle_scenario("multiple_vehicles")["actual"] == ("INDEPENDENT_ACTIVE_BINDINGS")
