import pytest

from vehicletrust import create_app
from vehicletrust.extensions import db
from vehicletrust.services import seed_demo


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
            "CHALLENGE_TTL_SECONDS": 30,
            "DEMO_MODE": True,
            "DEMO_ADMIN_TOKEN": "vehicletrust-test-admin",
        }
    )
    with application.app_context():
        db.drop_all()
        db.create_all()
        seed_demo()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def ctx(app):
    with app.app_context():
        yield
