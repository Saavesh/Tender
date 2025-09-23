# tests/test_routes_protected.py
import types
import pytest
from flask_security.utils import hash_password
from application.extensions import db, security
import application.routes as routes_module  # ensure routes registered
pytest.skip("Temporarily skipping auth-protected route tests while finishing setup.", allow_module_level=True)

@pytest.fixture(scope="function")
def authenticated_client(client, app):
    email = "testuser@example.com"
    password = "password123"

    # Create the user in an app context
    with app.app_context():
        ds = security.datastore
        user = ds.find_user(email=email)
        if not user:
            user = ds.create_user(email=email,
                                  password=hash_password(password),
                                  active=True)
            db.session.commit()

    # Log in via the real /login endpoint (Flask-Security)
    resp = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,   # so we land on a 200 page
    )
    assert resp.status_code == 200

    yield client

    # Teardown: remove the user so tests are isolated
    with app.app_context():
        u = security.datastore.find_user(email=email)
        if u:
            security.datastore.delete_user(u)
            db.session.commit()


def test_profile_page_with_authenticated_user(authenticated_client):
    resp = authenticated_client.get("/profile")
    assert resp.status_code == 200
    assert b"Your Profile" in resp.data
    assert b"testuser@example.com" in resp.data


def test_start_swiping_authenticated(authenticated_client):
    resp = authenticated_client.get("/start_swiping")
    assert resp.status_code == 200
    assert b"Create a Room" in resp.data


def test_profile_page_with_anonymous_user(client):
    resp = client.get("/profile", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location


def test_create_new_room_mocks_api(monkeypatch, authenticated_client):
    # Fake requests.get to avoid real HTTP
    def fake_get(url, params=None, timeout=None):
        data = {
            "results": [
                {
                    "place_id": "mock-1",
                    "name": "Mock Bistro",
                    "types": ["restaurant", "food"],
                    "price_level": 2,
                    "user_ratings_total": 123,
                    "rating": 4.4,
                    "photos": [{"photo_reference": "phref"}],
                },
                {
                    "place_id": "mock-2",
                    "name": "Test Trattoria",
                    "types": ["restaurant", "italian"],
                    "price_level": 1,
                    "user_ratings_total": 45,
                    "rating": 4.1,
                    "photos": [],
                },
            ]
        }
        return types.SimpleNamespace(
            status_code=200,
            json=lambda: data,
            raise_for_status=lambda: None,
        )

    # Patch requests.get as used by application.routes
    monkeypatch.setattr(routes_module.requests, "get", fake_get)

    # Create a room (auth required)
    resp = authenticated_client.post("/create_new_room", data={"location": "Anywhere"})
    assert resp.status_code in (302, 303)
    assert "/room/" in (resp.headers.get("Location") or "")