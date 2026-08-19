from vehicletrust.services import run_lifecycle_scenario


def test_old_plate_uid_is_operationally_retired_after_number_sale(ctx):
    result = run_lifecycle_scenario("sell_plate_number")
    assert result["details"]["old_result"] == "RETIRED_PHYSICAL_PLATE"
    assert result["details"]["new_result"] == "VERIFIED"
