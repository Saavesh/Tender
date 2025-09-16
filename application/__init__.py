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
    migrate.init_app(app, db)
    cache.init_app(app)

    from .routes import register_routes
    register_routes(app)

    with app.app_context():
        from .models import User, Role
        from flask_security import SQLAlchemyUserDatastore
        user_datastore = SQLAlchemyUserDatastore(db, User, Role)
        security.init_app(app, user_datastore)

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