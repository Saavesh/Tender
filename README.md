<p align="center">
  <img src="application/static/images/tender_logo.png" alt="Tender Logo" width="120" style="border-radius: 50%;">
</p>

# Tender
A playful nod to the dating app Tinder. Tender is lightweight, interactive voting room app designed to help friends choose a restaurant together. Just like *Tinder* helps people match with potential dates by swiping, *Tender* helps groups of friends “match” with restaurants by swiping on local food spots. ***Our goal is simple: Less time deciding, more time connecting.***



## Features
- **Real-Time Voting Rooms:** Users can create rooms, vote on restaurants with friends, and share the room link to invite more friends
- **Live UI Updates:** The voting room polls the server every 5 seconds to show who has finished voting in real-time.
- **Dynamic "It's a Match!" Screen:** Animated results page that reveals the "matching" restaurant.
- **Google API integration:** Fetches live restaurant data from the Google Places API.
- **Secure User Authentication:** Full registration, login, and session management.
- **Test:** Includes automated tests with Pytest to ensure site reliability.


## Tech Stack
- **Backend**: Flask, Flask-Security-Too, SQLAlchemy, Alembic/Flask-Migrate
- **Frontend**: HTML, JS, CSS
- **Database**: SQLite
- **Api**: Google Places (via API_KEY)
- **Testing**: Pytest, pytest-flask
- **Deployment**: Render, Gunicorn

## Live Demo
Link to be directed to the site on Render -> [https://tender-l253.onrender.com](https://tender-l253.onrender.com)

![CreateRoom GIF](application/static/videos/create_room.gif)
![VotingRoom Gif](application/static/videos/voting_room.gif)
![Results GIF](application/static/videos/results.gif)

## Project structure

```bash
.
├── application/
│   ├── static/           # Front-end files -> CSS, JS, images, videos
│   ├── templates/        # HTML Page layouts shown to users
│   ├── __init__.py       # Starts the app & wires everything together
│   ├── extensions.py     # Sets up add-ons -> database, login, email, caching
│   ├── models.py         # The database shapes (what tables look like)
│   └── routes.py         # The app’s URLs and what each one does
├── instance/
│   └── .gitkeep          # Ensures instance folder is created
├── migrations/           # Instructions to create/update database
├── tests/                # Tests
├── run.py                # Run this to start the app for local development
├── requirements.txt      # Dependencies required for the local version
├── pytest.ini            # Settings for running the tests
└── .gitignore            # Git will ignore these files/not track
```

## Getting started
To run this project on your local machine, follow these steps:

#### 1. Clone the repository:
```
git clone https://github.com/Saavesh/Tender.git`
cd Tender
```

#### 2. Create and activate a virtual environment
  ```
  python3 -m venv venv
  source venv/bin/activate
  ```

#### 3.Install dependencies
  ```
  pip install -r requirements.txt
  ```

#### 4. Set up your `.env` file
    Create a `.env` file in the root directory and add your secret keys and Google API key.

#### 5. Initialize the database
```
flask db upgrade
```

#### 6. Run the application
```
flask run
```

### Acknowledgments
This app started as a group project at CU Boulder in our web development course. The original version was built with a great team of classmates who helped turn this silly idea into something real. While this version is a personal continuation, I’m grateful for my teammates’ contributions and for making the process genuinely fun to be part of.
 