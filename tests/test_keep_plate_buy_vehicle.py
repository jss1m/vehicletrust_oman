from vehicletrust.services import run_lifecycle_scenario


def test_keep_plate_when_buying_replacement_vehicle(ctx):
    assert run_lifecycle_scenario("keep_plate")["actual"] == "REBIND_SUCCESS_STATIC_CODE"
