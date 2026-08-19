from vehicletrust.services import run_lifecycle_scenario


def test_confirmed_identity_can_still_raise_stolen_vehicle_alert(ctx):
    assert run_lifecycle_scenario("stolen_vehicle")["actual"] == (
        "VERIFIED_IDENTITY_STOLEN_VEHICLE"
    )
