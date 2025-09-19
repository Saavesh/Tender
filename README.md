<p align="center">
  <img src="application/static/images/tender_logo.png" alt="Tender Logo" width="120" style="border-radius: 50%;">
</p>

# Tender
A playful nod to the dating app Tinder. Tender is lightweight, interactive voting room app designed to help friends choose a restaurant together. Just like *Tinder* helps people match with potential dates by swiping, *Tender* helps groups of friends “match” with restaurants by swiping on local food spots. ***Our goal is simple: Less time deciding, more time connecting.***



## Features
- **Secure User Authentication:** Full registration, login, and session management.
- **Real-Time Voting Rooms:** Users can create rooms and vote on restaurants with friends.
- **Live UI Updates:** The voting room polls the server every 5 seconds to show who has finished voting in real-time.
- **Dynamic "It's a Match!" Screen:** An engaging, animated results page that reveals the winning restaurant.
- **Google API integration:** Fetches live restaurant data from the Google Places API.
- **Comprehensive Test Suite:** Includes a full suite of automated tests with Pytest to ensure code quality and reliability.


## Tech Stack
- **Backend**: Flask, Flask-Security-Too, SQLAlchemy, Alembic/Flask-Migrate
- **Frontend**: HTML, JS, CSS
- **Database**: SQLite
- **Api**: Google Places (via API_KEY)
- **Testing**: Pytest, pytest-flask
- **Deployment**: Render, Gunicorn

## Getting Started
Link to be directed to the app on Render: [https://tender-l253.onrender.com](https://tender-l253.onrender.com)

## Local Setup
To run this project on your local machine, follow these steps:

#### 1. Clone the repository:
```
git clone https://github.com/your-username/Tender.git`
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

#### 6. Run the application:**
```
flask run
```

## Demo
Youtube link coming soon.

### Acknowledgments
This app started as a group project at CU Boulder in our web development course. The original version was built with a great team of classmates who helped turn this silly idea into something real. While this version is a personal continuation, I’m grateful for my teammates’ contributions and for making the process genuinely fun to be part of.
