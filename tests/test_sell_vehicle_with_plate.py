from vehicletrust.services import run_lifecycle_scenario


def test_vehicle_ownership_transfer_does_not_change_identity_binding(ctx):
    assert run_lifecycle_scenario("sell_vehicle_with_plate")["actual"] == (
        "OWNERSHIP_CHANGED_BINDING_REMAINS"
    )
