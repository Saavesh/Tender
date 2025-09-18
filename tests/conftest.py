# tests/conftest.py
import os
import sys
import pytest
from sqlalchemy.pool import StaticPool

# Make sure the app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from application import create_app
from application.extensions import db


@pytest.fixture(scope="session")
def app():
    app = create_app({
        "TESTING": True,
        "PROPAGATE_EXCEPTIONS": False,   # let error handlers run in tests
        "WTF_CSRF_ENABLED": False,
        "CACHE_TYPE": "NullCache",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",  # in-memory
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        },
        "SECURITY_SEND_REGISTER_EMAIL": False,
        "SECRET_KEY": "testing-secret",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()