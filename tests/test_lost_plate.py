from vehicletrust.services import run_lifecycle_scenario


def test_lost_physical_plate_is_denied_after_reissue(ctx):
    result = run_lifecycle_scenario("lost_plate")
    assert result["actual"] == "OLD_PLATE_LOST_NEW_PLATE_ISSUED"
    assert result["details"]["old_result"] == "LOST_PLATE"
