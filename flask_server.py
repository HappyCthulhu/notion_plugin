import json
import os
import signal
import sys

import psycopg2
from flask import Flask
from flask_apscheduler import APScheduler
from flask_cors import CORS, cross_origin
from notifiers import get_notifier

from collect_pages_for_removing import collect_pages_for_removing, logger
from logging_settings import set_logger
from notion_tracking import notion_tracking

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# TODO: запросов к серверу многовато, имхо

# TODO: вот это все тоже в переменные среды вынести
new_pages_file = 'new_notion_pages.json'
pages_for_removing_file = 'pages_for_removing.json'
scheduler = APScheduler()


def get_conn_and_cursor():
    conn = psycopg2.connect(host=os.environ['DB_HOST_NAME'], user=os.environ['DB_USER_NAME'],
                            password=os.environ['DB_PASSWORD'], dbname=os.environ['DB_NAME'])
    cursor = conn.cursor()
    conn.set_client_encoding('UTF8')
    return conn, cursor


@app.route("/add")
@cross_origin()
def add_pages():
    # TODO: допилить
    cursor.execute(f"SELECT title, link FROM new_pages;")
    new_pages = cursor.fetchall()
    if new_pages:
        new_pages = json.dumps([{'title': page[0], 'page_url': page[1]} for page in new_pages], ensure_ascii=False)
        logger.info(f'New pages из базы: {new_pages}')

        telegram = get_notifier('telegram')
        telegram.notify(
            message=f'New pages из базы: {new_pages}', token=os.environ['TELEGRAM_KEY'],
            chat_id=os.environ['TELEGRAM_CHAT_ID'])

        cursor.execute(f'TRUNCATE TABLE new_pages CASCADE')
        conn.commit()

        telegram.notify(
            message='В данный момент база должна быть пуста', token=os.environ['TELEGRAM_KEY'],
            chat_id=os.environ['TELEGRAM_CHAT_ID'])
        logger.debug('В данный момент база должна быть пуста')
        return new_pages

    return {}


@app.route("/remove")
@cross_origin()
def remove_pages():
    with open(pages_for_removing_file, 'r') as file:
        pages_for_removing = file.read()

    with open(pages_for_removing_file, 'w') as file:
        json.dump({}, file)

    return pages_for_removing


def signal_handler(signal, frame):
    # close the socket here

    conn.close()
    logger.info('DB connection was closed')
    sys.exit(0)


if __name__ == "__main__":
    conn, cursor = get_conn_and_cursor()

    logger = set_logger()

    signal.signal(signal.SIGINT, signal_handler)
    scheduler.add_job(id='notion_tracking task', func=notion_tracking, trigger='interval', seconds=120)
    scheduler.add_job(id='collect_pages_for_removing task', func=collect_pages_for_removing, trigger='interval',
                      seconds=10)
    scheduler.start()
    app.run(host='0.0.0.0')
