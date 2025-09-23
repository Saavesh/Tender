# application/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate
from flask_security import Security

try:
    from flask_mailman import Mail
except ImportError:
    Mail = None

db = SQLAlchemy()
cache = Cache()
migrate = Migrate()
security = Security()
mail = Mail() if Mail else None