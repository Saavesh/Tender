# tests/conftest.py

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from application import create_app

@pytest.fixture(scope='module')
def app():
    """Create an instance of the Flask app with TESTING config."""
    app = create_app()
    app.config.update({
        "TESTING": False,
    })

    # Push the application context so things like `current_app` work
    with app.app_context():
        yield app


@pytest.fixture(scope='module')
def client(app):
    """Return a test client for the app."""
    return app.test_client()