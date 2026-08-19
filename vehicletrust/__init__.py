import os
import secrets
from pathlib import Path

from flask import Flask

from .extensions import db


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", f"sqlite:///{Path(app.instance_path) / 'vehicletrust.db'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CHALLENGE_TTL_SECONDS=int(os.getenv("CHALLENGE_TTL_SECONDS", "30")),
        MAX_CREDENTIAL_BYTES=4_096,
        DEMO_MODE=os.getenv("DEMO_MODE", "true").lower() in {"1", "true", "yes"},
        DEMO_ADMIN_TOKEN=os.getenv("DEMO_ADMIN_TOKEN"),
        GENERATE_QR_IMAGES=True,
        TESTING=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    from .routes import bp

    app.register_blueprint(bp)
    with app.app_context():
        db.create_all()
        from .services import seed_demo

        seed_demo()
    return app
