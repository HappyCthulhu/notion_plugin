from backend.models import db, NewNotionPages
from app import app
from flask_migrate import Migrate

db.init_app(app)

migrate = Migrate(app, db)