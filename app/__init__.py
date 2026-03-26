import os
import logging

from flask import Flask
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.environ.get('DB_PATH', '/data/guitar.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    from app.database import init_db
    init_db(app)

    from app.routes.matches import matches_bp
    from app.routes.searches import searches_bp
    from app.routes.settings import settings_bp
    app.register_blueprint(matches_bp)
    app.register_blueprint(searches_bp)
    app.register_blueprint(settings_bp)

    # Start scheduler only once (guard against Werkzeug reloader double-spawn)
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from app.scheduler import start_scheduler
        start_scheduler(app)

    return app
