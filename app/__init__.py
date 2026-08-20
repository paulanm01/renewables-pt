import os

from flask import Flask

from app.config import Config
from app.extensions import db, migrate


def create_app(config_class=Config):
    """Build the Flask app. Used by run.py and by the scripts."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Show accented characters as they are instead of escaping them,
    # so "Eólica" reads properly in the JSON responses.
    app.json.ensure_ascii = False

    # Attach the extensions to THIS app instance. Until now db and
    # migrate existed but were not connected to anything.
    db.init_app(app)
    migrate.init_app(app, db)

    # Imported for the side effect only: loading these modules is what
    # registers the tables with SQLAlchemy. Without this, Flask-Migrate
    # would generate empty migrations.
    from app.models import production, weather  # noqa: F401

    from app.routes.api import bp as api_bp
    app.register_blueprint(api_bp)

    from app.routes.views import bp as views_bp
    app.register_blueprint(views_bp)

    # Only start the scheduler in the main process. With debug=True,
    # Flask runs two processes (one just watches for code changes),
    # and without this check the job would run twice a day.
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from app.scheduler import start_scheduler
        start_scheduler(app)

    return app