# application/__init__.py

from flask import Flask
from dotenv import load_dotenv
import logging
from logging import StreamHandler
import os

from .extensions import db, cache, migrate, security  # <-- from new file

def create_app(testing=False):
    load_dotenv()
    app = Flask(__name__)
    if testing:
        app.config["TESTING"] = True

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECURITY_PASSWORD_SALT=os.getenv("SECURITY_PASSWORD_SALT"),
        SECURITY_PASSWORD_HASH="bcrypt",
        SECURITY_REGISTERABLE=True,
        CACHE_TYPE="SimpleCache",
        CACHE_DEFAULT_TIMEOUT=300,
    )

    # Bind extensions to app
    db.init_app(app)
    cache.init_app(app)

    # IMPORT MODELS EARLY to avoid circular issues with Flask-Security
    from .models import User, Role
    from flask_security import SQLAlchemyUserDatastore
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)

    # NOW bind migrate (after models are known to db)
    migrate.init_app(app, db)

    # Initialize Flask-Security with user_datastore
    security.init_app(app, user_datastore)

    # Register routes
    from .routes import register_routes
    register_routes(app)

    # Logging
    if not app.debug:
        handler = StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Tender app startup complete")

    return app