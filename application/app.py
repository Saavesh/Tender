###############################################################################
## app.py
##
## This script represents the main entry point for the Tender web app. It 
## contains all database schema and Flask routes used to implement the full
## functionality of the user registration/login, room creation, as well as all
## database connections to deal with guest users and voting room logic.
##
## Authors: Sherry Saavedra, Tyler Teichmann, Seth Ely
## Date: 11/26/2024
##
## Usage:
##   This web app is currently being run using Render. As such, the following
##   commands must be added to the Render Web Service:
##     - Build Command: `pip install -r application/requirements`
##     - Start Command: `python application/app.py`
##
## NOTE:
##   The routes are laid out in the following structure:
##   1. Core Routes
##     - Basic routes for rendering the main pages of the website
##   2. User Management
##     - Routes for managing authenticated user profiles
##   3. Room Webpage Routes
##     - Routes for rendering the voting room in its different states
##   4. Guest User Data Routes
##     - Routes for managing database connections in regard to guest users
##       and display names used for each room
##   5. Room Data Routes
##     - Routes for managing database connections used for the room logic 
###############################################################################

###############################################################################
## Required Modules
###############################################################################
from flask import Flask, url_for, render_template, redirect, flash, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, hash_password, RegisterForm, LoginForm
from flask_security.models import fsqla_v3 as fsqla
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import requests
import uuid
import logging

###############################################################################
## App Configuration
##
## This section initializes the Flask application and configures its settings, 
## including the database connection and Flask-Security settings.
###############################################################################
# Flask app initialization
app = Flask(__name__)

api_key = os.getenv("API_KEY", "")

# Flask app configurations
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", 'e29936d5d1cd5fee7a80863ad58307e9')
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", 'my_salt_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'argon2'
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_CHANGEABLE'] = True
app.config['WTF_CSRF_ENABLED'] = False

# Yelp API key
api_key = os.getenv("API_KEY")

# Set Flask logger to debug
app.logger.setLevel(logging.DEBUG)

# Set werkzeug logger (used for HTTP requests) to debug
logging.getLogger('werkzeug').setLevel(logging.DEBUG)

# Set Flask-Security logger to debug
security_logger = logging.getLogger('flask_security')
security_logger.setLevel(logging.DEBUG)

# Initialize database
db = SQLAlchemy(app)

# Define models
fsqla.FsModels.set_db_info(db)

###############################################################################
## Models
##
## Defines the database schema
###############################################################################
class Role(db.Model, fsqla.FsRoleMixin):
    # use the default model for flask security
    pass

# authenticated users (can create and host rooms)
class User(db.Model, fsqla.FsUserMixin):
    # use the default model for flask security
    pass

# used for guest users to join rooms without be authenticated users
class GuestUser(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    Username = db.Column(db.String(150), nullable=False)
    RoomID = db.Column(db.String(36), db.ForeignKey('room.RoomID'), nullable=False)
    done = db.Column(db.Boolean, nullable=False, default=False)

# Restaurant table populated with data taken from the Yelp API
class Restaurant(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    RoomID = db.Column(db.Integer, db.ForeignKey('room.RoomID'), nullable=False)
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
    WinningRestaurant = db.Column(db.String(50), db.ForeignKey('restaurant.id'), nullable=True)
    restaurants = db.relationship('Restaurant', backref='room', lazy=True, foreign_keys='Restaurant.RoomID')
    votes = db.relationship('Vote', backref='room', lazy=True)

# Votes tied to a user, room, and restaurant
class Vote(db.Model):
    VoteID = db.Column(db.String(36), primary_key=True)
    GuestUserID = db.Column(db.Integer, db.ForeignKey('guest_user.id'), nullable=False)
    RoomID = db.Column(db.String(36), db.ForeignKey('room.RoomID'), nullable=False)
    RestaurantID = db.Column(db.String(50), db.ForeignKey('restaurant.id'), nullable=False)  # Use Restaurant ID
    VoteChoice = db.Column(db.Integer, nullable=False)  # Enum: 1 (Yum), 0 (Meh), -1 (Ew)
    VoteTime = db.Column(db.DateTime, default=datetime.utcnow)

###############################################################################
## Initialize the database
###############################################################################
# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Database setup
with app.app_context():
    db.create_all()
    if not user_datastore.find_user(email="test@me.com"):
        user_datastore.create_user(email="test@me.com", password=hash_password("password"))
    db.session.commit()

###############################################################################
###############################################################################
## Core Routes
###############################################################################
###############################################################################

@app.errorhandler(500)
def internal_error(error):
    return str(error), 500

###############################################################################
## Route: /
##
## Homepage for the application
##
## Methods: GET
##
## Parameters: None
##
## Returns: Renders the "index.html" template.
###############################################################################
@app.route("/")
def index():
    return render_template("index.html")

###############################################################################
## Route: /about
##
## Displays the "About" page with information about the application
##
## Methods: GET
##
## Parameters: None
##
## Returns: Renders the "about.html" template
###############################################################################
@app.route("/about")
def about():
    return render_template("about.html")

###############################################################################
## Room Webpage Routes
###############################################################################
###############################################################################

###############################################################################
## Route: /start_swiping_now
##
## Purpose: Redirects the user to their current active room or displays an
##          error message if no active room is found.
##
## Methods: GET
##
## Parameters: None
##
## Returns: 
##   - Redirects to the current active room if found.
##   - If no active room exists, flashes an error message and redirects to the 
##     profile page.
###############################################################################
@app.route('/start_swiping_now')
@auth_required()
def start_swiping_now():
    # Step 1. Query the database for the user's active room
    current_room = Room.query.filter_by(HostUserID=current_user.id, RoomStatus="active").first()
    
    # Step 2. Redirect to the room if found
    if current_room:
        return redirect(url_for('room', roomid=current_room.RoomID))
    
    # Step 3. Flash an error message if no active room is found
    flash("No active room found. Create or join a room first!", "error")
    return redirect(url_for('profile'))


###############################################################################
###############################################################################
## Function: contact()
##
## Purpose: Displays a contact form and sends messages
##
## Methods: GET, POST
##
## Parameters: 
##   - name (string): name entered on the form
##   - email (string): email address entered on the form
##   - message (string): message entered on the form
##
## Returns: 
##   Renders the "contact.html" for GET requests or redirects to the contact 
##   page with a success message for POST requests.
###############################################################################
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        # Handle the form data (log it, store it, send an email, etc.)
        flash("Thank you for your message!", "success")

        # Redirect to the contact page or another page after submission
        return redirect(url_for("contact"))

    return render_template("contact.html")

###############################################################################
###############################################################################
## User Management
###############################################################################
###############################################################################

###############################################################################
## Function: profile()
##
## Purpose: Displays the profile page for the logged-in user
##
## Methods: GET
##
## Parameters: None
##
## Returns: 
##   Renders the "profile.html" template with user data and room info
###############################################################################
@app.route("/profile")
@auth_required()
def profile():
    ## Step 1.
    ##   Get all rooms from the current user id
    ## Step 2.
    ##   Iterate through each room, parsing the room data to the rooms_data array
    ## Step 3.
    ##   Checks for winning restaurant, and retrieves the winning restaurant
    ##   from the restaurant table to add the name and url of the restaurant
    ## Step 4.
    ##   Render the profile template passing through the user and room info
    
    rooms = Room.query.filter_by(HostUserID=current_user.id).all()

    rooms_data = []

    for room in rooms:
        room_data = {
            'RoomID': room.RoomID,
            'RoomCreated': room.RoomCreated,
            'RoomStatus': room.RoomStatus,
            'Location': room.Location,
            'WinningRestaurant': None,
            'Link': url_for('room', roomid=room.RoomID),
        }

        # Fetch the winning restaurant
        if room.RoomStatus == 'inactive' and room.WinningRestaurant:
            winning_restaurant = Restaurant.query.get(room.WinningRestaurant)
            if winning_restaurant:
                room_data['WinningRestaurantName'] = winning_restaurant.name
                room_data['WinningRestaurantURL'] = winning_restaurant.url

        rooms_data.append(room_data)



    return render_template(
        "profile.html",
        user=current_user,
        rooms_data=rooms_data
    )

###############################################################################
## Route: /update_email
##
## Purpose: Allows authenticated users to update their email address
##
## Methods: POST
##
## Parameters: 
##   - email (string): The new email address to update
##
## Returns: 
##   - Success: Flash message indicating the email was updated
##   - Failure: Flash message indicating a valid email was not provided
###############################################################################
@app.route("/update_email", methods=["POST"])
@auth_required()  # Ensure only logged-in users can update their email
def update_email():
    new_email = request.form.get("email")
    if new_email:
        current_user.email = new_email
        db.session.commit()
        flash("Email updated successfully!", "success")
    else:
        flash("Please provide a valid email.", "danger")
    return redirect(url_for("profile"))

###############################################################################
## Route: /logout
##
## Purpose: Logs out the currently authenticated user.
##
## Methods: GET
##
## Parameters: None
##
## Returns: Redirects to the index page with a flash message confirming logout.
###############################################################################
@app.route("/logout")
@auth_required()
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

###############################################################################
###############################################################################
## Room Webpage Routes
###############################################################################
###############################################################################

###############################################################################
## Route: /start_swiping
##
## Purpose: Serves the page for initiating the process to create a new room.
##
## Methods: GET
##
## Parameters: None
##
## Returns: Renders the "create_room.html" template.
###############################################################################
@app.route('/start_swiping')
@auth_required()
def start_swiping():
    return render_template("create_room.html")

###############################################################################
## get_restaurant_data(location)
##
## Makes a connection to the Yelp API and returns a list of five restaurants
## for the given location
##
## Parameters: 
##   - location (string): the location entered on the form
##
## Returns: A python dictionary of the restaurant including the following keys:
##          - id (string): id of the restaurant in the Yelp API
##          - name (string): name of the restaurant
##          - url (string): link to the website of the restaurant
##          - categories (array): an array of dictionaries containing category 
##            information of the restaurant
##          - price (string): price in number of dollar signs (e.g. '$$')
##          - review_count (int): number of reviews for the restaurant
##          - rating (int): the rating for the restaurant out of 5.0
##          
##          If invalid response, returns an empty dictionary
###############################################################################
def get_restaurant_data(location):
    ## Step 1.
    ##   Make the API call with the appropriate headers and parameters
    ## Step 2.
    ##   If the response is valid, filter only the desired keys from the data
    ##   and return the restaurant dictionary
    
    url = 'https://api.yelp.com/v3/businesses/search'
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {'term': 'restaurants', 'location': location, 'limit': 5}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        restaurants = []
        fields = ["id", "name", "image_url", "url", "categories", "price", "review_count", "rating"]
        for restaurant in response.json()['businesses']:
            new_restaurant = {key: restaurant[key] for key in fields if key in restaurant}
            restaurants.append(new_restaurant)
        return restaurants
    return {}

###############################################################################
## Route: /create_new_room
##
## Purpose: Create a new room if an authenticated user
##
## Methods: POST
##
## Parameters:
##   - location (string): The location to search for restaurants
##
## Returns: Redirects to the newly created room page
###############################################################################
@app.route("/create_new_room", methods=['POST'])
@auth_required()
def create_new_room():
    ## Step 1.
    ##   Use the location and the helper function get_restaurant_data to 
    ##   retrieve list of restaurant data for the room
    ## Step 2.
    ##   Create and commit a new room using the current user id, location and
    ##   generate a unique room id using uuid4
    ## Step 3.
    ##   Create a new restaurant entry in the restaurant table for each
    ##   restaurant retrieved from the Yelp API
    ## Step 4.
    ##   Redirect to the newly created room
    
    location = request.form['location']
    restaurant_list = get_restaurant_data(location)
    
    # Create a new room
    new_room = Room(
        HostUserID=current_user.id, 
        Location=location, 
        RoomID=str(uuid.uuid4())
    )
    db.session.add(new_room)
    db.session.commit()
    
    
    # Add restaurants
    for restaurant in restaurant_list:
        new_restaurant = Restaurant(
            RoomID=new_room.RoomID,
            id=str(uuid.uuid4()), # unique id, not yelp id to handle duplicates
            name=restaurant['name'],
            image_url=restaurant['image_url'],
            url=restaurant['url'],
            categories=json.dumps(restaurant['categories']), # serialize to json string
            price=restaurant.get('price'),
            review_count=restaurant['review_count'],
            rating=restaurant['rating']
        )
        db.session.add(new_restaurant)

    db.session.commit()
    flash('Room created successfully!', 'success')
    return redirect(url_for('room', roomid=new_room.RoomID))

###############################################################################
## Route: /room/<roomid>
##
## This is the most complicated route and handles all voting room logic. It 
## renders a different template depending on the state of the room and whether
## or not the user has created a displayname.
##
## Methods: GET
##
## Parameters:
##   - roomid (string): The ID of the room to access
##
## Returns: 
##   Depending on the state of the room, will render the following:
##     - If voting for the room has ended:
##         The results page for the room
##     - If the room is active and the user has not set a displayname:
##         The user entry form for the user to create a displayname
##     - If the room is active and the user has a displayname:
##         The voting room passing through the appropriate variables
###############################################################################
@app.route('/room/<string:roomid>')
def room(roomid):
    # Step 1.
    #   Attempt to get the cookie containing the displayname and the room from
    #   the room table
    # Step 2.
    #   If the room is found and inactive:
    #     - retrieve the entry in the restaurant table using the foreign key 
    #       'room.WinningRestaurant' and create a dictionary of its attributes
    #     - retrieve all restaurants associated with the room
    #     - retrieve all votes for the room and create a dictionary that has
    #       each restaurant vote for each user
    #     - render the results template, passing through the previous data
    # Step 3.
    #   If the room is active and a cookie with the user id is not present:
    #     - render the user-entry template that prompts the user to create a
    #       display name
    # Step 4.
    #   If the room is active and a cookie with the user id is present:
    #     - retrieve and serialize the restaurant data for the room as well as
    #     - retrieve and serialize the guest user info from the cookie id value
    #     - retrieve any votes already cast by user and remove them from the
    #       restaurant data passed through to the room
    #     - render the room template with the appropriate room and user data

    # Get the room and cookie
    guest_user_id = request.cookies.get('GuestUserID')
    room = Room.query.get(roomid)
    if not room:
        flash("Room not found.", "danger")
        return redirect(url_for('index'))
    
    # Check if the room is inactive
    if room.RoomStatus == "inactive":
        # get and parse the winning restaurant data
        winning_restaurant = Restaurant.query.filter_by(id=room.WinningRestaurant, RoomID=roomid).first()
        winning_restaurant_data = None
        if winning_restaurant:
            winning_restaurant_data = {
                "id": winning_restaurant.id,
                "name": winning_restaurant.name,
                "image_url": winning_restaurant.image_url,
                "url": winning_restaurant.url,
                "categories": [],
                "price": winning_restaurant.price,
                "review_count": winning_restaurant.review_count,
                "rating": winning_restaurant.rating
            }
            if winning_restaurant.categories:
                winning_restaurant_data["categories"] = json.loads(winning_restaurant.categories)

        # Get all votes for the room
        votes = Vote.query.filter_by(RoomID=roomid).all()

        # capture restaurant ids and names in a dict
        restaurants = {}
        for restaurant in Restaurant.query.filter_by(RoomID=roomid).all():
            restaurants[restaurant.id] = restaurant.name

        # iterate through each vote and create a dictionary for each user
        # containing the vote choice of each restaurant
        # e.g. {"bob": {"McDonalds": -1, "burger king": 1}, "seth": {"McDonalds": -1, "burger king": 1} }
        user_votes = {}
        for vote in votes:
            user = GuestUser.query.get(vote.GuestUserID)
            if user:
                if user.Username not in user_votes:
                    # create empty dictionary for each new user found
                    user_votes[user.Username] = {}
                restaurant_name = restaurants.get(vote.RestaurantID, "Unknown")
                user_votes[user.Username][restaurant_name] = vote.VoteChoice

        # render the results template for completed room
        return render_template(
            "results.html",
            room=room,
            winning_restaurant=winning_restaurant_data,
            restaurant_names=list(restaurants.values()),
            user_votes=user_votes
        )
    
    # if active and no cookie is detected, render the user-entry form page
    elif not guest_user_id:
        return render_template(
            "user-entry.html",
            room=room
        )
    
    # if active and cookie is detected with user id:
    else:
        # get all restaurants associated with the room
        all_restaurants = Restaurant.query.filter_by(RoomID=roomid).all()
        # populate the restaurant_data dictionary with the data for each restaurant
        restaurant_data = []
        for restaurant in all_restaurants:
            restaurant_entry = {
                "id": restaurant.id,
                "name": restaurant.name,
                "image_url": restaurant.image_url,
                "url": restaurant.url,
                "categories": [],
                "price": restaurant.price,
                "review_count": restaurant.review_count,
                "rating": restaurant.rating
            }
            if restaurant.categories:
                restaurant_entry["categories"] = json.loads(restaurant.categories)
            restaurant_data.append(restaurant_entry)

        # find the user info using the cookie that has user id
        guest_user = GuestUser.query.filter_by(id=guest_user_id, RoomID=roomid).first()
        if guest_user:
            guest_user_serialized = {
                "id": guest_user.id,
                "Username": guest_user.Username,
                "RoomID": guest_user.RoomID,
                "done": guest_user.done
            }
            
            # get all votes already cast by the user and remove from restaurant data
            # so no duplicate votes are cast when refreshed
            votes = Vote.query.filter_by(RoomID=roomid, GuestUserID=guest_user_id).all()
            for vote in votes:
                for restaurant in restaurant_data[:]:
                    if restaurant['id'] == vote.RestaurantID:
                        restaurant_data.remove(restaurant)
                    
                    
        else:
            flash("Invalid guest user ID for this room. Please rejoin.", "danger")
            return redirect(url_for('index'))

        # render the voting room
        return render_template(
            "room.html",
            room=room,
            restaurant_data=restaurant_data,
            current_guest_user=guest_user_serialized
        )



###############################################################################
###############################################################################
## Guest User Data Routes
###############################################################################
###############################################################################

###############################################################################
## Route: /add_guest_user
##
## Purpose: Adds a new guest user to a room and sets a cookie with the user id
##
## Methods: POST
##
## Parameters:
##   - Username (string): The username of the guest user
##   - RoomID (string): The ID of the room to join
##
## Returns: Redirects to the voting room page
###############################################################################
@app.route('/add_guest_user', methods=['POST'])
def add_guest_user():
    # Step 1.
    #   Capture username and room id values from the form and check they are
    #   valid
    # Step 2.
    #   Create a new entry in the guest user table
    # Step 3.
    #   create a response object using make_response.set_cookie that will
    #   reload the page and serve a cookie with the user id
    #   (on reload, the room route will render the voting room)
    
    username = request.form.get('Username')
    room_id = request.form.get('RoomID') 
    if not username or not room_id:
        return jsonify({"error": "Username and RoomID are required"}), 400

    # Create a new guest user with a unique ID
    new_user = GuestUser(
        id=str(uuid.uuid4()),  # Generate a unique ID for the user
        Username=username,
        RoomID=room_id,
        done=False
    )
    db.session.add(new_user)
    db.session.commit()

    # Create the response object that will redirect and serve the cookie
    response = make_response(redirect(f'/room/{room_id}'))
    response.set_cookie('GuestUserID', new_user.id, max_age=7 * 24 * 60 * 60, path=f'/room/{room_id}')
    return response

###############################################################################
## Route: /set_guest_done
##
## Purpose: Marks a guest user as "done" indicating they have finished voting
##
## Methods: POST
##
## Parameters:
##   - GuestUserID (string): The ID of the guest user to mark as done
##
## Returns: JSON response indicating success or failure
###############################################################################
@app.route('/set_guest_done', methods=['POST'])
def set_guest_done():
    # Step 1.
    #   Parse the request from json object
    # Step 2.
    #   Retrieve the user entry from the guest user table
    # Step 3.
    #   update the done attribute to true
    
    data = request.get_json()
    guest_user_id = data.get('GuestUserID')

    if not guest_user_id:
        return jsonify({"error": "GuestUserID is required"}), 400

    # Fetch the guest user by ID
    guest_user = GuestUser.query.get(guest_user_id)
    if not guest_user:
        return jsonify({"error": "Guest user not found"}), 404

    # Update the 'done' status
    guest_user.done = True
    db.session.commit()

    return jsonify({"message": "Guest user status updated successfully."})

    
###############################################################################
## Route: /get_room_users
##
## Purpose: Gets the list of users in a specific room
##
## Methods: GET
##
## Parameters:
##   - RoomID (string): The ID of the room
##
## Returns: JSON response with user details
###############################################################################
@app.route('/get_room_users', methods=['GET'])
def get_room_users():
    # Step 1.
    #   attempt to get the room id and retrieve the room data from the room table
    # Step 2.
    #   Attempt to get the list of guest users using the 
    # Step 3.
    #   serialize the data for each user
    # Step 4.
    #   return the jsonified user data
    
    room_id = request.args.get('RoomID')
    if not room_id:
        return jsonify({"error": "Room ID is required"}), 400

    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    try:
        # Query GuestUser table for users in the given room
        guest_users = GuestUser.query.filter_by(RoomID=room_id).all()

        # Format the response
        users_data = []
        for guest in guest_users:
            users_data.append({
                "Username": guest.Username,
                "done": guest.done,
                "id": guest.id
            })

        return jsonify(users_data)  # Return the list of users with their done status
    except Exception as e:
        return jsonify({"error": "Failed to fetch room users", "details": str(e)}), 500
    


###############################################################################
###############################################################################
## Room Data Routes
###############################################################################
###############################################################################
    
###############################################################################
## Route: /finalize_room
##
## Purpose: Finalizes a room and determines the winning restaurant
##
## Methods: POST
##
## Parameters:
##   - roomId (string): The ID of the room to finalize
##
## Returns: JSON response with winning restaurant details
###############################################################################
@app.route('/finalize_room', methods=['POST'])
@auth_required()
def finalize_room():
    # Step 1.
    #   get the room from the request data (sent as json)
    # Step 2.
    #   Get all votes associated with the given room
    # Step 3.
    #   iterate through all votes and tabulate results in the vote_counts dict
    # Step 4.
    #   determine the winning restaurant using the max value in the dict
    # Step 5.
    #   Retrieve the winning restaurant from the restaurant table
    # Step 6.
    #   Set the status of the room to inactive
    # Step 7.
    #   return the json response

    # get the room data from the request json
    data = request.get_json()
    room_id = data.get('roomId')
    room = Room.query.get(room_id)
    if not room or room.HostUserID != current_user.id:
        return jsonify({'message': 'Unauthorized or room not found.'}), 403

    # get all votes for the room
    votes = Vote.query.filter_by(RoomID=room_id).all()
    
    # create vote dictionary
    vote_counts = {}
    # iterate through votes, using the vote choice values to increment/decrement
    # the value for each restaurant id
    for vote in votes:
        if vote.RestaurantID not in vote_counts:
            vote_counts[vote.RestaurantID] = 0
        vote_counts[vote.RestaurantID] += vote.VoteChoice

    # Determine the winning restaurant using max
    winning_restaurant_id = max(vote_counts, key=vote_counts.get, default=None)
    # get the winning restaurant data
    winning_restaurant = Restaurant.query.get(winning_restaurant_id)
    # set the id of the winning restaurant if found
    room.WinningRestaurant = winning_restaurant_id if winning_restaurant else None
    
    # set room to inactive to indicate that voting has ended
    room.RoomStatus = 'inactive'
    db.session.commit()

    # Return the winning restaurant details
    return jsonify({
        'message': 'Room finalized.',
        'winning_restaurant': winning_restaurant.name if winning_restaurant else None,
        'room_id': room_id
    }), 200

###############################################################################
## Route: /get_user_rooms
##
## Purpose: Retrieves all rooms created by the currently authenticated user
##
## Methods: GET
##
## Parameters: None
##
## Returns: JSON response containing the user's rooms and their details
###############################################################################
@app.route('/get_user_rooms', methods=['GET'])
@auth_required()
def get_user_rooms():
    rooms = Room.query.filter_by(HostUserID=current_user.id).all()
    rooms_data = [
        {
            'RoomID': room.RoomID,
            'RoomCreated': room.RoomCreated,
            'RoomStatus': room.RoomStatus,
            'Location': room.Location,
            'WinningRestaurant': room.WinningRestaurant
        }
        for room in rooms
    ]
    return jsonify(rooms_data)

###############################################################################
## Route: /get_room_status
##
## Purpose: Retrieves the current status of a specific room
##
## Methods: GET
##
## Parameters:
##   - RoomID (string): The ID of the room to check
##
## Returns: JSON response containing the room's status
###############################################################################
@app.route('/get_room_status', methods=['GET'])
def get_room_status():
    room_id = request.args.get('RoomID')
    if not room_id:
        return jsonify({"error": "Room ID is required"}), 400

    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    return jsonify({"roomStatus": room.RoomStatus}), 200

###############################################################################
###############################################################################
## Vote Data Routes
###############################################################################
###############################################################################

###############################################################################
## Route: /create_vote
##
## Purpose: Creates a vote for a restaurant in a room by a guest user
##
## Methods: POST
##
## Parameters:
##   - RoomID (string): The ID of the room
##   - GuestUserID (string): The ID of the guest user
##   - RestaurantID (string): The ID of the restaurant being voted on
##   - VoteChoice (int): The vote value (-1 for "Ew", 0 for "Meh", 1 for "Yum")
##
## Returns: JSON response indicating success or failure
###############################################################################
@app.route('/create_vote', methods=['POST'])
def create_vote():
    # Step 1.
    #   Parse the data passed as json
    # Step 2.
    #   validate the vote choice is either -1, 0 or 1
    # Step 3.
    #   Get the room, restaurant, and guest user data and validate they exist
    # Step 4.
    #   create a new entry in the vote table
    # Step 5.
    #   return the json response
    
    data = request.json
    room_id = data.get('RoomID')
    guest_user_id = data.get('GuestUserID')
    restaurant_id = data.get('RestaurantID')
    vote_choice = data.get('VoteChoice')

    if vote_choice not in [-1, 0, 1]:
        return jsonify({"error": "Invalid vote choice. Must be -1, 0, or 1."}), 400

    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found."}), 404

    restaurant = Restaurant.query.filter_by(id=restaurant_id, RoomID=room_id).first()
    if not restaurant:
        return jsonify({"error": "Invalid restaurant choice."}), 400

    guest_user = GuestUser.query.get(guest_user_id)
    if not guest_user or guest_user.RoomID != room_id:
        return jsonify({"error": "Guest user not authorized for this room."}), 403

    new_vote = Vote(
        VoteID=str(uuid.uuid4()),
        GuestUserID=guest_user.id,
        RoomID=room_id,
        RestaurantID=restaurant_id,
        VoteChoice=vote_choice
    )
    db.session.add(new_vote)
    db.session.commit()

    return jsonify({"message": "Vote successfully created."}), 201


###############################################################################
## Route: /get_room_votes
##
## Purpose: Fetches all votes for a specific room.
##
## Methods: GET
##
## Parameters:
##   - RoomID (string): The ID of the room
##
## Returns: JSON response containing the votes for the room
###############################################################################
@app.route('/get_room_votes', methods=['GET'])
def get_room_votes():
    room_id = request.args.get('RoomID')
    votes = Vote.query.filter_by(RoomID=room_id).all()

    votes_data = []
    for vote in votes:
        votes_data.append({
            'VoteID': vote.VoteID,
            'Username': vote.Username,
            'RestaurantName': vote.RestaurantName,
            'VoteChoice': vote.VoteChoice,
            'VoteTime': vote.VoteTime
        })

    return jsonify(votes_data)


###############################################################################
## Route: /rooms
##
## Purpose: Displays the user's active and inactive rooms on a dedicated page. 
##          Allows users to view details of existing rooms, navigate to active 
##          rooms, or create a new room. The rooms are sorted by creation date, 
##          and only the last 10 rooms (active and inactive) are displayed.
##
## Methods: GET
##
## Parameters: None
##
## Returns:
##   - Renders the "rooms.html" template.
##       - Displays two separate tables:
##           1. Active Rooms: Shows rooms with a status of "active".
##           2. Inactive Rooms: Shows rooms with a status of "inactive".
##       - Includes an option at the top to create a new room, regardless of 
##         whether active rooms exist.
###############################################################################    
@app.route('/rooms', methods=["GET", "POST"])
@auth_required()
def rooms():
    # Fetch active and inactive rooms
    active_rooms = Room.query.filter_by(HostUserID=current_user.id, RoomStatus="active").order_by(Room.RoomCreated.desc()).limit(10).all()
    inactive_rooms = Room.query.filter_by(HostUserID=current_user.id, RoomStatus="inactive").order_by(Room.RoomCreated.desc()).limit(10).all()

    # Add dynamic links to rooms
    for room in active_rooms:
        room.Link = url_for('room', roomid=room.RoomID)
    for room in inactive_rooms:
        room.Link = url_for('room', roomid=room.RoomID)

    return render_template(
        "rooms.html",
        active_rooms=active_rooms,
        inactive_rooms=inactive_rooms
    )


###############################################################################
## Main Driver Function
##
## Runs the Flask application on a local server.
##
## Usage:
##   Run `python app.py` to start the server on the specified port.
###############################################################################
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3308, debug=True)
