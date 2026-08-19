from vehicletrust import create_app
from vehicletrust.models import Credential, Vehicle
from vehicletrust.services import seed_demo


def test_fresh_database_seed_and_restart(tmp_path):
    database = tmp_path / "fresh.db"
    config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}"}
    first = create_app(config)
    with first.app_context():
        seed_demo()
        assert Vehicle.query.count() == 3
        assert Credential.query.count() == 2
    second = create_app(config)
    with second.app_context():
        assert Vehicle.query.count() == 3
        assert Credential.query.count() == 2
    assert second.test_client().get("/health").status_code == 200


def test_all_required_pages_respond(client):
    paths = [
        "/",
        "/dashboard",
        "/vehicles",
        "/vehicles/VT-7A82F1",
        "/credentials/issue",
        "/verify",
        "/security-lab",
        "/audit",
        "/architecture",
        "/security-design",
        "/rebind",
        "/lifecycle",
    ]
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, path
        assert b"Research Prototype" in response.data
