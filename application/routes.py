#application/routes.py
# standard library
import json
import logging
import os
import uuid

# Third-party
import requests
from flask import (
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_security import auth_required, current_user, logout_user, hash_password

# Local/application
from application.extensions import db, cache, security
from .models import GuestUser, Restaurant, Room, Vote

# ===================================================================================
# Route registrations
# ===================================================================================


def register_routes(app):
    @cache.memoize(3600)
    def get_restaurant_data(location):
        """Fetches restaurant data from the Google Places API."""
        api_key = os.getenv("API_KEY")
        if not api_key:
            logging.error("API Key for Google Places not found!")
            return []

        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"restaurants in {location}",
            "key": api_key,
            "type": "restaurant",
        }
        try:
            response = requests.get(search_url, params=params, timeout=5)
            response.raise_for_status()
            results = response.json().get("results", [])

            formatted_restaurants = []
            for place in results[:10]:
                photo_url = None
                if "photos" in place and len(place["photos"]) > 0:
                    photo_ref = place["photos"][0]["photo_reference"]
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={api_key}"

                formatted_restaurants.append(
                    {
                        "id": place.get("place_id"),
                        "name": place.get("name"),
                        "image_url": photo_url,
                        "url": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}",
                        "categories": [{"title": t} for t in place.get("types", [])],
                        "price_level": place.get("price_level"),
                        "review_count": place.get("user_ratings_total", 0),
                        "rating": place.get("rating", 0),
                    }
                )
            return formatted_restaurants

        except requests.exceptions.RequestException as e:
            logging.error("Error fetching data from Google Places API: %s", e)
            return []

    # --------------------- User-Facing Routes ---------------------

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            flash("Thank you for your message!", "success")
            return redirect(url_for("contact"))
        return render_template("contact.html")

    @app.route("/profile")
    @auth_required()
    def profile():
        rooms = (
            Room.query.filter_by(HostUserID=current_user.id)
            .order_by(Room.RoomCreated.desc())
            .all()
        )
        rooms_data = []
        for room in rooms:
            room_info = {
                "RoomID": room.RoomID,
                "RoomCreated": room.RoomCreated.strftime("%Y-%m-%d %H:%M"),
                "RoomStatus": room.RoomStatus,
                "Location": room.Location,
                "WinningRestaurantName": None,
                "Link": url_for("room", roomid=room.RoomID),
            }
            if room.RoomStatus == "inactive" and room.WinningRestaurant:
                winning_restaurant = Restaurant.query.get(room.WinningRestaurant)
                if winning_restaurant:
                    room_info["WinningRestaurantName"] = winning_restaurant.name
            rooms_data.append(room_info)
        return render_template("profile.html", user=current_user, rooms_data=rooms_data)

    @app.route("/logout")
    @auth_required()
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/start_swiping")
    @auth_required()
    def start_swiping():
        return render_template("create_room.html")

    @app.route("/rooms")
    @auth_required()
    def rooms():
        """Renders the page showing the user's active and inactive rooms."""
        active_rooms = (
            Room.query.filter_by(HostUserID=current_user.id, RoomStatus="active")
            .order_by(Room.RoomCreated.desc())
            .limit(10)
            .all()
        )
        inactive_rooms = (
            Room.query.filter_by(HostUserID=current_user.id, RoomStatus="inactive")
            .order_by(Room.RoomCreated.desc())
            .limit(10)
            .all()
        )
        return render_template(
            "rooms.html", active_rooms=active_rooms, inactive_rooms=inactive_rooms
        )

    @app.route("/room/<string:roomid>")
    def room(roomid):
        room = Room.query.get_or_404(roomid)
        guest_user_id = request.cookies.get(f"guest_user_id_{roomid}")

        if room.RoomStatus == "inactive":
            winning_restaurant = (
                Restaurant.query.get(room.WinningRestaurant)
                if room.WinningRestaurant
                else None
            )
            votes = Vote.query.filter_by(RoomID=roomid).all()
            restaurants = {r.id: r.name for r in room.restaurants}
            user_votes = {}
            for vote in votes:
                user = GuestUser.query.get(vote.GuestUserID)
                if user:
                    if user.Username not in user_votes:
                        user_votes[user.Username] = {}
                    restaurant_name = restaurants.get(vote.RestaurantID, "Unknown")
                    user_votes[user.Username][restaurant_name] = vote.VoteChoice

            return render_template(
                "results.html",
                room=room,
                winning_restaurant=winning_restaurant,
                user_votes=user_votes,
                restaurant_names=list(restaurants.values()),
            )

        if not guest_user_id:
            return render_template("user-entry.html", room=room)

        guest_user = GuestUser.query.get(guest_user_id)
        if not guest_user or guest_user.RoomID != roomid:
            response = make_response(redirect(url_for("room", roomid=roomid)))
            response.delete_cookie(f"guest_user_id_{roomid}")
            flash(
                "There was an issue with your session. Please enter your name again.",
                "warning",
            )
            return response

        voted_restaurant_ids = [
            v.RestaurantID for v in Vote.query.filter_by(GuestUserID=guest_user.id)
        ]
        restaurants_to_vote = [
            r for r in room.restaurants if r.id not in voted_restaurant_ids
        ]

        return render_template(
            "room.html",
            room=room,
            restaurant_data=restaurants_to_vote,
            current_guest_user=guest_user,
        )

    # --------------------- Auth & Profile Updates ---------------------

    @app.route("/update_email", methods=["POST"])
    @auth_required()
    def update_email():
        new_email = request.form.get("email")
        if new_email:
            current_user.email = new_email
            db.session.commit()
            flash("Email updated successfully!", "success")
        else:
            flash("Please provide a valid email.", "danger")
        return redirect(url_for("profile"))

    @app.route("/create_new_room", methods=["POST"])
    @auth_required()
    def create_new_room():
        location = request.form["location"]
        restaurant_list = get_restaurant_data(location)

        if not restaurant_list:
            flash(
                f"Could not find any restaurants for '{location}'. Please try a different location.",
                "danger",
            )
            return redirect(url_for("start_swiping"))

        new_room = Room(HostUserID=current_user.id, Location=location)
        db.session.add(new_room)

        for restaurant_data in restaurant_list:
            restaurant = Restaurant.query.get(restaurant_data.get("id"))
            if not restaurant:
                restaurant = Restaurant(
                    id=restaurant_data.get("id"),
                    name=restaurant_data.get("name"),
                    image_url=restaurant_data.get("image_url"),
                    url=restaurant_data.get("url"),
                    categories=json.dumps(restaurant_data.get("categories", [])),
                    price_level=restaurant_data.get("price_level"),
                    review_count=restaurant_data.get("review_count"),
                    rating=restaurant_data.get("rating"),
                )
                db.session.add(restaurant)
            new_room.restaurants.append(restaurant)

        db.session.commit()
        flash("Room created successfully!", "success")
        return redirect(url_for("room", roomid=new_room.RoomID))

    # --------------------- API Routes ---------------------

    @app.route("/add_guest_user", methods=["POST"])
    def add_guest_user():
        username = request.form.get("Username")
        room_id = request.form.get("RoomID")
        if not username or not room_id:
            return jsonify({"error": "Username and RoomID are required"}), 400

        new_user = GuestUser(id=str(uuid.uuid4()), Username=username, RoomID=room_id)
        db.session.add(new_user)
        db.session.commit()

        response = make_response(redirect(url_for("room", roomid=room_id)))
        response.set_cookie(
            f"guest_user_id_{room_id}", new_user.id, max_age=7 * 24 * 60 * 60
        )
        return response

    @app.route("/create_vote", methods=["POST"])
    def create_vote():
        data = request.get_json(silent=True) or {}
        room_id = data.get("RoomID")
        guest_user_id = data.get("GuestUserID")
        restaurant_id = data.get("RestaurantID")
        vote_choice = data.get("VoteChoice")

        # required fields (allow 0 as valid vote)
        if (
            room_id is None
            or guest_user_id is None
            or restaurant_id is None
            or vote_choice is None
        ):
            return jsonify({"error": "Missing required data."}), 400

        # coerce vote to int and validate
        try:
            vote_choice = int(vote_choice)
        except (TypeError, ValueError):
            return jsonify({"error": "VoteChoice must be an integer."}), 400
        if vote_choice not in (-1, 0, 1):
            return jsonify({"error": "Invalid vote choice."}), 400

        # Checks - room, guest user in room, restaurant in room
        room = Room.query.get(room_id)
        if not room or room.RoomStatus != "active":
            return jsonify({"error": "Room not found or not active."}), 400
        guest = GuestUser.query.get(guest_user_id)
        if not guest or guest.RoomID != room_id:
            return jsonify({"error": "Guest not found or not in this room."}), 400
        if not any(r.id == restaurant_id for r in room.restaurants):
            return jsonify({"error": "Restaurant not in this room."}), 400

        # create
        existing = Vote.query.filter_by(
            GuestUserID=guest_user_id, RoomID=room_id, RestaurantID=restaurant_id
        ).first()
        if existing:
            existing.VoteChoice = vote_choice
        else:
            db.session.add(
                Vote(
                    VoteID=str(uuid.uuid4()),
                    GuestUserID=guest_user_id,
                    RoomID=room_id,
                    RestaurantID=restaurant_id,
                    VoteChoice=vote_choice,
                )
            )

        db.session.commit()
        return jsonify({"message": "Vote recorded."}), 201

    @app.route("/set_guest_done", methods=["POST"])
    def set_guest_done():
        data = request.get_json()
        guest_user_id = data.get("GuestUserID")
        if not guest_user_id:
            return jsonify({"error": "GuestUserID is required"}), 400

        guest_user = GuestUser.query.get(guest_user_id)
        if not guest_user:
            return jsonify({"error": "Guest user not found"}), 404

        guest_user.done = True
        db.session.commit()
        return jsonify({"message": "Guest user status updated successfully."})

    @app.route("/get_room_users", methods=["GET"])
    def get_room_users():
        room_id = request.args.get("RoomID")
        if not room_id:
            return jsonify({"error": "Room ID is required"}), 400

        users = GuestUser.query.filter_by(RoomID=room_id).all()
        users_data = [
            {"Username": u.Username, "done": u.done, "id": u.id} for u in users
        ]
        return jsonify(users_data)

    @app.route("/get_room_status", methods=["GET"])
    def get_room_status():
        room_id = request.args.get("RoomID")
        if not room_id:
            return jsonify({"error": "Room ID is required"}), 400
        room = Room.query.get_or_404(room_id)
        return jsonify({"roomStatus": room.RoomStatus})

    @app.route("/finalize_room", methods=["POST"])
    @auth_required()
    def finalize_room():
        data = request.get_json()
        room_id = data.get("roomId")
        room = Room.query.get(room_id)
        if not room or room.HostUserID != current_user.id:
            return jsonify({"message": "Unauthorized or room not found."}), 403

        votes = Vote.query.filter_by(RoomID=room_id).all()
        if not votes:
            room.WinningRestaurant = None
        else:
            vote_counts = {}
            for vote in votes:
                vote_counts[vote.RestaurantID] = (
                    vote_counts.get(vote.RestaurantID, 0) + vote.VoteChoice
                )
            winning_restaurant_id = max(vote_counts, key=vote_counts.get)
            room.WinningRestaurant = winning_restaurant_id

        room.RoomStatus = "inactive"
        db.session.commit()
        return jsonify({"message": "Room finalized."}), 200

    @app.route("/trigger-500")
    def trigger_500():
        raise RuntimeError("Simulated Server Error")

    # --------------------- Error Handlers & CLI ---------------------

    @app.errorhandler(500)
    def internal_error(error):
        logging.error("500 Error: %s", error)
        return render_template("500.html"), 500

    @app.errorhandler(404)
    def page_not_found(_error):
        logging.warning("404 Not Found: %s", request.url)
        return render_template("404.html"), 404

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        user_datastore = security.datastore
        if not user_datastore.find_user(email="test@me.com"):
            user_datastore.create_user(
                email="test@me.com", password=hash_password("password")
            )
        db.session.commit()
        print("Database initialized.")
