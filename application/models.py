# application/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_security.models import fsqla_v3 as fsqla
from datetime import datetime
import uuid

db = SQLAlchemy()

# Define models for Flask-Security
fsqla.FsModels.set_db_info(db)

class Role(db.Model, fsqla.FsRoleMixin):
    pass

class User(db.Model, fsqla.FsUserMixin):
    pass

# Guest users who can join rooms without a full account
class GuestUser(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    Username = db.Column(db.String(150), nullable=False)
    RoomID = db.Column(db.String(36), db.ForeignKey('room.RoomID'), nullable=False)
    done = db.Column(db.Boolean, nullable=False, default=False)

# Stores restaurant data fetched from the API
room_restaurants_association = db.Table('room_restaurants',
    db.Column('room_id', db.String(36), db.ForeignKey('room.RoomID'), primary_key=True),
    db.Column('restaurant_id', db.String(255), db.ForeignKey('restaurant.id'), primary_key=True)
)

class Restaurant(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    # RoomID is no longer needed here
    name = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    categories = db.Column(db.Text, nullable=True)
    price_level = db.Column(db.Integer, nullable=True)
    review_count = db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Float, nullable=True)

class Room(db.Model):
    RoomID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    HostUserID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    RoomCreated = db.Column(db.DateTime, default=datetime.utcnow)
    RoomStatus = db.Column(db.String(50), default='active')
    Location = db.Column(db.String(150))
    WinningRestaurant = db.Column(db.String(255), db.ForeignKey('restaurant.id'), nullable=True)
    # Update the relationship to use the association table
    restaurants = db.relationship('Restaurant', secondary=room_restaurants_association, lazy='subquery',
        backref=db.backref('rooms', lazy=True))
    votes = db.relationship('Vote', backref='room', lazy=True)


# Stores individual votes tied to a user, room, and restaurant
class Vote(db.Model):
    VoteID = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    GuestUserID = db.Column(db.String(36), db.ForeignKey('guest_user.id'), nullable=False)
    RoomID = db.Column(db.String(36), db.ForeignKey('room.RoomID'), nullable=False)
    RestaurantID = db.Column(db.String(255), db.ForeignKey('restaurant.id'), nullable=False)
    VoteChoice = db.Column(db.Integer, nullable=False)  # 1 (Yum), 0 (Meh), -1 (Ew)
    VoteTime = db.Column(db.DateTime, default=datetime.utcnow)