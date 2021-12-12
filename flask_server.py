import json
import os
import signal
import sys

import psycopg2
from flask import Flask
from flask_apscheduler import APScheduler
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from notifiers import get_notifier
from sqlalchemy import create_engine

from collect_pages_for_removing import collect_pages_for_removing, logger
from logging_settings import set_logger
from notion_tracking import notion_tracking

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# TODO: этот файл нужно переименовать

# TODO: как чувак без app хуярит?
db = SQLAlchemy(app)

POSTGRES = {
    'user': os.environ['DB_USER_NAME'],
    'pw': os.environ['DB_PASSWORD'],
    'db': os.environ['DB_NAME'],
    'host': os.environ['DB_HOST_NAME'],
    'port': '5432',
}
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:\
%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES

import models
# AllNotionPages.query.all()
test_shit = db.session.query(models.AllNotionPages).filter_by(title='дела/it/проекты').first()
test_link = test_shit.link
pass


engine = create_engine("postgresql+psycopg2://postgres:12345@localhost/notion_plugin")
engine.connect()
print(engine)
connection = engine.raw_connection()
connection.set_client_encoding('UTF8')

# TODO: почему здесь все еще присутствуют json-файлы? У нас же есть ДБ
# TODO: вот это все тоже в переменные среды вынести
new_pages_file = 'new_notion_pages.json'
pages_for_removing_file = 'pages_for_removing.json'
scheduler = APScheduler()


@app.route("/add")
@cross_origin()
def add_pages():
    # TODO: допилить
    cursor = connection.cursor()
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
        connection.commit()

        telegram.notify(
            message='В данный момент база должна быть пуста', token=os.environ['TELEGRAM_KEY'],
            chat_id=os.environ['TELEGRAM_CHAT_ID'])
        logger.debug('В данный момент база должна быть пуста')
        return new_pages

    return {}


@app.route("/remove")
@cross_origin()
def remove_pages():
    cursor = connection.cursor()
    cursor.execute(f"SELECT bookmark_id FROM bookmarks_for_remove;")
    bookmarks_for_remove = cursor.fetchall()
    if bookmarks_for_remove:
        bookmarks_for_remove = json.dumps([bookmark_id[0] for bookmark_id in bookmarks_for_remove], ensure_ascii=False)
        print(f'bookmarks_for_remove: {bookmarks_for_remove}')
        logger.info(f'Закладки для удаления из базы: {bookmarks_for_remove}')

        telegram = get_notifier('telegram')
        telegram.notify(
            message=f'Закладки для удаления из базы: {bookmarks_for_remove}', token=os.environ['TELEGRAM_KEY'],
            chat_id=os.environ['TELEGRAM_CHAT_ID'])

        cursor.execute(f'TRUNCATE TABLE bookmarks_for_remove CASCADE')
        connection.commit()

        telegram.notify(
            message='В данный момент база "bookmarks_for_remove" должна быть пуста', token=os.environ['TELEGRAM_KEY'],
            chat_id=os.environ['TELEGRAM_CHAT_ID'])
        logger.debug('В данный момент база "bookmarks_for_remove" должна быть пуста')

        return bookmarks_for_remove

    return {}


def signal_handler(signal, frame):
    # close the socket here

    # conn = get_db()
    # cursor = conn.cursor()
    connection.close()
    logger.info('DB connection was closed')
    sys.exit(0)


#
# def get_conn_and_cursor():
#     conn = psycopg2.connect(host=os.environ['DB_HOST_NAME'], user=os.environ['DB_USER_NAME'],
#                             password=os.environ['DB_PASSWORD'], dbname=os.environ['DB_NAME'])
#     cursor = conn.cursor()
#     conn.set_client_encoding('UTF8')
#     return conn, cursor
#
# conn, cursor = get_conn_and_cursor()
#
# TODO: походу то, что ниже этого комментария не исполняется вообще. Лол. Не могу вспомнить, что и зачем здесь делал вообще
if __name__ == "__main__":
    # conn, cursor = get_conn_and_cursor()
    logger = set_logger()

    signal.signal(signal.SIGINT, signal_handler)
    scheduler.add_job(id='notion_tracking task', func=notion_tracking, trigger='interval', seconds=120)
    scheduler.add_job(id='collect_pages_for_removing task', func=collect_pages_for_removing, trigger='interval',
                      seconds=10)
    scheduler.start()
    app.run(host='0.0.0.0')
