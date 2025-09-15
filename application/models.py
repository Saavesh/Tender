# application/models.py
from . import db
from flask_security.models import fsqla_v3 as fsqla
import uuid
from datetime import datetime

# Allow Flask-Security to access the db object
fsqla.FsModels.set_db_info(db)


###############################################################################
## Models
## Defines the database schema
## Use the default model for flask security
###############################################################################

class Role(db.Model, fsqla.FsRoleMixin):
    pass

class User(db.Model, fsqla.FsUserMixin):
    pass

# used for guest users to join rooms without be authenticated users
class GuestUser(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    Username = db.Column(db.String(150), nullable=False)
    RoomID = db.Column(db.String(36), db.ForeignKey('room.RoomID'), nullable=False)
    done = db.Column(db.Boolean, nullable=False, default=False)

# Restaurant table populated with data 
class Restaurant(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    RoomID = db.Column(db.String(36), db.ForeignKey('room.RoomID'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    categories = db.Column(db.Text, nullable=True)
    price = db.Column(db.String(10), nullable=True)
    review_count = db.Column(db.Integer, nullable=True)
    rating = db.Column(db.Float, nullable=True)

# All data for each room
class Room(db.Model):
    RoomID = db.Column(db.String(36), primary_key=True)
    HostUserID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    RoomCreated = db.Column(db.DateTime, default=datetime.utcnow)
    RoomStatus = db.Column(db.String(50), default='active')
    Location = db.Column(db.String(150))
    WinningRestaurant = db.Column(db.String(36), db.ForeignKey('restaurant.id'), nullable=True)
    restaurants = db.relationship('Restaurant', backref='room', lazy=True, foreign_keys='Restaurant.RoomID')
    votes = db.relationship('Vote', backref='room', lazy=True)

# Votes tied to a user, room, and restaurant
class Vote(db.Model):
    VoteID = db.Column(db.String(36), primary_key=True)
    GuestUserID = db.Column(db.String(36), db.ForeignKey('guest_user.id'), nullable=False)
    RoomID = db.Column(db.String(36), db.ForeignKey('room.RoomID'), nullable=False)
    RestaurantID = db.Column(db.String(36), db.ForeignKey('restaurant.id'), nullable=False)
    VoteChoice = db.Column(db.Integer, nullable=False) # Enum: 1 (Yum), 0 (Meh), -1 (Ew)
    VoteTime = db.Column(db.DateTime, default=datetime.utcnow)