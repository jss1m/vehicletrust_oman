from vehicletrust.models import PhysicalPlate, PlateVehicleBinding
from vehicletrust.services import run_lifecycle_scenario


def test_database_blocks_two_active_bindings_for_one_plate(ctx):
    assert run_lifecycle_scenario("duplicate_binding")["actual"] == "BLOCKED"
    for plate in PhysicalPlate.query.all():
        assert (
            PlateVehicleBinding.query.filter_by(physical_plate_id=plate.id, status="ACTIVE").count()
            <= 1
        )
