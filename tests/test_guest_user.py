import uuid
from application.models import GuestUser


def test_add_guest_user(client, app):
    room_id = str(uuid.uuid4())
    # Pre-create the room
    with app.app_context():
        from application.models import Room
        from application.extensions import db

        db.session.add(Room(RoomID=room_id, HostUserID="dummy", Location="Test"))
        db.session.commit()

    response = client.post(
        "/add_guest_user", data={"Username": "TestGuest", "RoomID": room_id}
    )

    assert response.status_code == 302  # Redirect after adding guest user
    cookie_name = f"guest_user_id_{room_id}"
    assert cookie_name in response.headers.get("Set-Cookie", "")

    # Check DB
    with app.app_context():
        user = GuestUser.query.filter_by(RoomID=room_id, Username="TestGuest").first()
        assert user is not None


def test_set_guest_done(client, app):
    guest_id = str(uuid.uuid4())
    with app.app_context():
        from application.extensions import db

        db.session.add(GuestUser(id=guest_id, Username="DoneTester", RoomID="r123"))
        db.session.commit()

    response = client.post("/set_guest_done", json={"GuestUserID": guest_id})
    assert response.status_code == 200
    assert b"updated successfully" in response.data

    with app.app_context():
        updated = GuestUser.query.get(guest_id)
        assert updated.done is True


def test_get_room_users(client, app):
    room_id = "test_room"
    with app.app_context():
        from application.extensions import db

        db.session.add(
            GuestUser(
                id=str(uuid.uuid4()), Username="Alice", RoomID=room_id, done=False
            )
        )
        db.session.add(
            GuestUser(id=str(uuid.uuid4()), Username="Bob", RoomID=room_id, done=True)
        )
        db.session.commit()

    response = client.get(f"/get_room_users?RoomID={room_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2
    usernames = [u["Username"] for u in data]
    assert "Alice" in usernames
    assert "Bob" in usernames
