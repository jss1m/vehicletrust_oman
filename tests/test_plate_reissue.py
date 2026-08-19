from vehicletrust.services import run_lifecycle_scenario


def test_damaged_plate_reissue_changes_plate_uid(ctx):
    assert run_lifecycle_scenario("plate_replacement")["actual"] == (
        "OLD_PLATE_REPLACED_NEW_PLATE_ISSUED"
    )
