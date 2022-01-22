import json
import os
import signal
import sys

from flask_apscheduler import APScheduler
from flask_cors import cross_origin
from notifiers import get_notifier

from app import app, db
from collect_pages_for_removing import collect_pages_for_removing, logger
from models import NewNotionPages, BookmarksForRemove
from notion_tracking import notion_tracking


@app.route("/add")
@cross_origin()
def add_pages():
    # TODO: Забить в models.py метод для возвращения json?
    new_pages = NewNotionPages.query.all()
    if new_pages:
        new_pages = json.dumps([{'title': page.title, 'page_url': page.link} for page in new_pages], ensure_ascii=False)
        logger.info(f'New pages из базы: {new_pages}')

        telegram = get_notifier('telegram')
        telegram.notify(
            message=f'New pages из базы: {new_pages}', token=os.environ['TELEGRAM_KEY'],
            chat_id=os.environ['TELEGRAM_CHAT_ID'])

        NewNotionPages.query.delete()
        db.session.commit()

        telegram.notify(
            message='В данный момент база должна быть пуста', token=os.environ['TELEGRAM_KEY'],
            chat_id=os.environ['TELEGRAM_CHAT_ID'])
        logger.debug('В данный момент база должна быть пуста')
        return new_pages

    return {}


@app.route("/remove")
@cross_origin()
def remove_pages():
    bookmarks_for_remove = BookmarksForRemove.query.all()

    if bookmarks_for_remove:
        bookmarks_for_remove = json.dumps([bookmark.bookmark_id for bookmark in bookmarks_for_remove],
                                          ensure_ascii=False)
        print(f'bookmarks_for_remove: {bookmarks_for_remove}')
        logger.info(f'Закладки для удаления из базы: {bookmarks_for_remove}')

        telegram = get_notifier('telegram')
        telegram.notify(
            message=f'Закладки для удаления из базы: {bookmarks_for_remove}', token=os.environ['TELEGRAM_KEY'],
            chat_id=os.environ['TELEGRAM_CHAT_ID'])

        BookmarksForRemove.query.delete()
        db.session.commit()

        telegram.notify(
            message='В данный момент база "bookmarks_for_remove" должна быть пуста', token=os.environ['TELEGRAM_KEY'],
            chat_id=os.environ['TELEGRAM_CHAT_ID'])
        logger.debug('В данный момент база "bookmarks_for_remove" должна быть пуста')

        return bookmarks_for_remove

    return {}


def signal_handler(signal, frame):
    db.session.close()
    logger.info('DB connection was closed')
    sys.exit(0)


if __name__ == "__main__":
    print('Запускаем шедулеры')
    signal.signal(signal.SIGINT, signal_handler)

    scheduler = APScheduler()
    scheduler.add_job(id='notion_tracking task', func=notion_tracking, trigger='interval', seconds=120)
    scheduler.add_job(id='collect_pages_for_removing task', func=collect_pages_for_removing, trigger='interval',
                      seconds=10)
    scheduler.start()
    app.run(host='0.0.0.0', debug=True)
