# application/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from flask_caching import Cache
import os

# Initialize extensions so they can be imported by other files
db = SQLAlchemy()
security = Security()
cache = Cache()

def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)

    # Load configuration from environment variables
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'a-default-secret-key-for-dev')
    app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", 'a-default-salt-for-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Flask-Security-Too configurations
    app.config['SECURITY_REGISTERABLE'] = True
    app.config['SECURITY_PASSWORD_HASH'] = 'argon2'
    app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
    app.config['SECURITY_CHANGEABLE'] = True
    app.config['WTF_CSRF_ENABLED'] = False # Recommended to set to True for production
    
    # Flask-Caching configuration
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 3600 # Cache for 1 hour

    # Initialize extensions with the app instance
    db.init_app(app)
    cache.init_app(app)

    with app.app_context():
        # Import parts of our application
        from . import routes
        from . import models

        # Setup Flask-Security
        user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
        security.init_app(app, user_datastore)

        # Create database tables for our models
        db.create_all()

        return app