# run.py
from application import create_app
from flask_migrate import upgrade

app = create_app()

# Auto-run migrations on startup (for Render or production deployment)
try:
    with app.app_context():
        upgrade()
except Exception as e:
    print(f"Migration failed: {e}")

if __name__ == "__main__":
    app.run(debug=True)