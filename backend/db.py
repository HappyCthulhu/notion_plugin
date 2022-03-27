from flask_migrate import Migrate

from app import app
from backend.models import db

db.init_app(app)

migrate = Migrate(app, db)
