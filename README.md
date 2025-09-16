<p align="center">
  <img src="application/static/images/tender_logo.png" alt="Tender Logo" width="120" style="border-radius: 50%;">
</p>

# Tender
A playful nod to the dating app Tinder. Tender is lightweight, interactive voting room app designed to help friends choose a restaurant together. Just like *Tinder* helps people match with potential dates by swiping, *Tender* helps groups of friends “match” with restaurants by swiping on local food spots. ***Our goal is simple: Less time deciding, more time connecting.***



## Project Description
Tender is a web-based app where users log in with a group of people (or just one friend) and are shown cards featuring local restaurants in their area. Each member swipes left for "yum" or right for "gross" on each restaurant. After everyone has voted, the app calculates scores and recommends a selection for the group. Some features include:
- Group-based restaurant voting rooms
- Swipe interface for quick decision-making
- Score-based restaurant recommendation
- Google API integration for real data


## Getting Started

### Option 1: Click on Link
Link to be directed to the app on Render: [https://tender-g7nq.onrender.com/](https://tender-g7nq.onrender.com/)

### Option 2: Run locally
Follow these steps and bash commands to get the Tender application running on your local machine (aka your computer)

**1. Prerequisites**
Make sure you have Python 3 and Git installed on your system.

**2. Clone the Repository**
Open your terminal and run the following bash command to clone the project and then go to that directory:

```
git clone https://github.com/Saavesh/Tender.git
cd Tender
```

**3. Set Up the Virtual Environment**
Create and activate a Python virtual environment to keep dependencies isolated to avoid making any changes to your system-wide programs.

```
# Create the virtual environment
python3 -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate

# Or on Windows
# venv\Scripts\activate
```

**4. Install Dependencies**
Install all the required packages using the requirements.txt file from the root of the project.

```
pip install -r requirements.txt
```

**5. Configure Environment Variables**
Create a file named .env in the root of your project folder and add the following content. Be sure to replace the placeholder values with your own.
```
# .env
SECRET_KEY='a_very_long_and_random_string_of_characters'
SECURITY_PASSWORD_SALT='another_long_and_random_string'
FLASK_APP=run.py
FLASK_ENV=development
SQLALCHEMY_DATABASE_URI='sqlite:///instance/site.db'
API_KEY='your_google_places_api_key_goes_here'
```

**6. Initialize and Upgrade the Database**
Run the following commands to set up your database schema.
```
# Run this command only once to create the migrations folder
flask db init

# Run these commands every time you change your models.py
flask db migrate -m "Initial database setup"
flask db upgrade
```

**7. Run the Application**
You can now start the Flask development server.
```
flask run
```
The application will be available at http://127.0.0.1:5000.


## Demo
Youtube link coming soon.

### Acknowledgments
This app started as a group project at CU Boulder in our web development course. The original version was built with a great team of classmates who helped turn this silly idea into something real. While this version is a personal continuation, I’m grateful for my teammates’ contributions and for making the process genuinely fun to be part of.
