from vehicletrust.services import run_lifecycle_scenario


def test_reserved_plate_never_returns_verified(ctx):
    assert run_lifecycle_scenario("sell_vehicle_keep_plate")["actual"] == "RESERVED_PLATE"
