from vehicletrust.services import run_lifecycle_scenario


def test_selling_vehicle_while_retaining_plate_reserves_it(ctx):
    assert run_lifecycle_scenario("sell_vehicle_keep_plate")["actual"] == "RESERVED_PLATE"
