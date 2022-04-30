import os
import signal
import sys

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from backend.helpers.logger_settings import logger
from backend.models import db
from backend.urls import api_bp
from make_celery import make_celery

# нужно исключительно для запуска flask run
if os.environ['APP_SETTINGS'] == 'Development':
    from config import DevelopmentConfig as Config

elif os.environ['APP_SETTINGS'] == 'Production':
    from config import Config


# TODO: config_filename? wtf

def create_app():
    app = Flask(__name__)

    app.register_blueprint(api_bp, url_prefix='/')
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    from backend.schema import ma
    ma.init_app(app)

    # preventing error "been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource"
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    return app


def signal_handler(signal, frame):
    db.session.close()
    logger.info('DB connection was closed')
    sys.exit(0)


app = create_app()
# TODO: Migrate не было в этом документе. Однако, когда она только в bd.py была, ничего не работало
migrate = Migrate(app, db)
celery = make_celery(app)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    # debug: нужно для запуска через python app.py. if подставляет определенный конфиг сюда
    app.run(host='0.0.0.0', debug=Config.DEBUG)
