from vehicletrust.services import run_lifecycle_scenario


def test_plate_number_sale_reissues_physical_identity(ctx):
    assert run_lifecycle_scenario("sell_plate_number")["actual"] == (
        "OLD_PLATE_RETIRED_NEW_PLATE_ISSUED"
    )
