import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object(os.environ['APP_SETTINGS'])

db = SQLAlchemy(app)

from flask_migrate import Migrate

migrate = Migrate(app, db)

from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

engine = create_engine(os.environ['DATABASE_URL'])
if not database_exists(engine.url):
    create_database(engine.url)
print(database_exists(engine.url))
