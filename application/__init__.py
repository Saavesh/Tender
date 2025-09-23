# application/__init__.py

# Standard library
import logging
import os
from logging import StreamHandler
# Third-party
from flask import Flask
from dotenv import load_dotenv
from flask_security import SQLAlchemyUserDatastore
# Local/application
from .extensions import db, cache, migrate, security, mail

def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    # Ensure instance folder exists (for SQLite file))
    os.makedirs(app.instance_path, exist_ok=True)

    # Base config
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SECURITY_PASSWORD_SALT=os.getenv("SECURITY_PASSWORD_SALT"),
        SECURITY_PASSWORD_HASH="bcrypt",
        SECURITY_REGISTERABLE=True,
        SECURITY_RECOVERABLE = True,# enables /forgot, /reset flows
        SECURITY_CHANGEABLE = True,# enables /change (when logged in)
        SECURITY_SEND_REGISTER_EMAIL=False,# Disable email confirmation for simplicity
        SECURITY_EMAIL_SENDER=os.getenv("SECURITY_EMAIL_SENDER", "no-reply@example.com"),
        SECURITY_POST_RESET_VIEW = "security.login",# where to go after successful reset
        CACHE_TYPE="SimpleCache",
        CACHE_DEFAULT_TIMEOUT=300,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Mail settings
        MAIL_BACKEND=os.getenv("MAIL_BACKEND", "console"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER", "no-reply@example.com"),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "localhost"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 1025)),
        MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "false").lower() == "true",
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_SUPPRESS_SEND=os.getenv("MAIL_SUPPRESS_SEND", "1") == "1",
    )
    # Normalize DB URI (default to instance/site.db for relative sqlite URIs)
    env_uri = os.getenv("SQLALCHEMY_DATABASE_URI")
    if env_uri:
        # Trust absolute sqlite (sqlite:////...)
        if env_uri.startswith("sqlite:////") or not env_uri.startswith("sqlite:///"):
            db_uri = env_uri
        else:
            # place DB in the instance folder
            db_uri = "sqlite:///" + os.path.join(app.instance_path, "site.db")
    else:
        db_uri = "sqlite:///" + os.path.join(app.instance_path, "site.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri

    # Allow tests to override (in-memory DB, disable CSRF)
    if test_config:
        app.config.update(test_config)

    # ----- Extensions -----
    db.init_app(app)
    cache.init_app(app)
    if mail:
        mail.init_app(app)

    # Import models before migrate so Alembic sees them
    from .models import User, Role
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)

    migrate.init_app(app, db)
    security.init_app(app, user_datastore)

    # ----- Routes -----
    from .routes import register_routes
    register_routes(app)

    # ----- Logging -----
    if not app.debug:
        handler = StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("Tender app startup complete")

    return app