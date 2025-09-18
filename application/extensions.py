# application/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_migrate import Migrate
from flask_security import Security

db = SQLAlchemy()
cache = Cache()
migrate = Migrate()
security = Security()