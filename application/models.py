# application/models.py

# Standard library
from datetime import datetime
import uuid
# Third-party
from flask_security.models import fsqla_v3 as fsqla
# Local/application
from .extensions import db
# Configure Flask-Security-Too to use SQLAlchemy instance
fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):
    __tablename__ = "role"
    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(db.Model, fsqla.FsUserMixin):
    __tablename__ = "user"
    def __repr__(self) -> str:
        return f"<User {self.email}>"


class GuestUser(db.Model):
    __tablename__ = "guest_user"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    Username = db.Column(db.String(150), nullable=False)
    RoomID = db.Column(db.String(36), db.ForeignKey("room.RoomID"), nullable=False)
    done = db.Column(db.Boolean, nullable=False, default=False)

    # ORM-only relationship back to Room
    room = db.relationship("Room", back_populates="guests")


# Association table: Room <-> Restaurant (many-to-many)
room_restaurants_association = db.Table(
    "room_restaurants",
    db.Column("room_id", db.String(36), db.ForeignKey("room.RoomID"), primary_key=True),
    db.Column("restaurant_id", db.String(255), db.ForeignKey("restaurant.id"), primary_key=True),
)

class Restaurant(db.Model):
    __tablename__ = "restaurant"

    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500))
    url = db.Column(db.String(500))
    categories = db.Column(db.Text)  # JSON string
    price_level = db.Column(db.Integer)
    review_count = db.Column(db.Integer)
    rating = db.Column(db.Float)

    def __repr__(self) -> str:
        return f"<Restaurant {self.name!r}>"


class Room(db.Model):
    __tablename__ = "room"

    RoomID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    HostUserID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    RoomCreated = db.Column(db.DateTime, default=datetime.utcnow)
    RoomStatus = db.Column(db.String(50), default="active")
    Location = db.Column(db.String(150))
    WinningRestaurant = db.Column(db.String(255), db.ForeignKey("restaurant.id"))

    restaurants = db.relationship(
        "Restaurant",
        secondary=room_restaurants_association,
        lazy="subquery",
        backref=db.backref("rooms", lazy=True),
    )
    votes = db.relationship(
        "Vote",
        backref="room",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=False,
    )
    guests = db.relationship(
        "GuestUser",
        back_populates="room",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=False,
    )

    def __repr__(self) -> str:
        return f"<Room {self.RoomID} status={self.RoomStatus}>"


class Vote(db.Model):
    __tablename__ = "vote"

    VoteID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    GuestUserID = db.Column(db.String(36), db.ForeignKey("guest_user.id"), nullable=False)
    RoomID = db.Column(db.String(36), db.ForeignKey("room.RoomID"), nullable=False)
    RestaurantID = db.Column(db.String(255), db.ForeignKey("restaurant.id"), nullable=False)
    VoteChoice = db.Column(db.Integer, nullable=False)  # -1, 0, or 1
    VoteTime = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Vote {self.VoteID} choice={self.VoteChoice}>"