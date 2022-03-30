import json
import os

from flask_restful import Resource
from notifiers import get_notifier
from sqlalchemy.orm import scoped_session

from backend.helpers.logger_settings import logger
# marshmello должен быть иницианизирован после sql_alchemy. Поэтому сначала импортим models, потом schema
from backend.models import db, NewNotionPages, BookmarksForRemove
from backend.schema import NewPagesSchema, BookmarksSchema


class AddPages(Resource):
    def __init__(self):
        self.new_pages_schema = NewPagesSchema(many=True)

    session: scoped_session = db.session

    def get(self):
        try:
            # скорее всего, проблема отсутствия часть записей из бд в закладках была в том, что delete стоял гораздо ниже
            # Он опустошал базу, в которой были данные, появившиеся после NewNotionPages.query.all()
            new_pages: dict = NewNotionPages.query.all()
            NewNotionPages.query.delete()
            db.session.commit()

            if new_pages:
                new_pages_schema = self.new_pages_schema.dump(new_pages)
                logger.info(f'New pages из базы: {new_pages_schema}')

                telegram = get_notifier('telegram')
                telegram.notify(
                    message=f'New pages из базы: {new_pages}', token=os.environ['TELEGRAM_KEY'],
                    chat_id=os.environ['TELEGRAM_CHAT_ID'])


                telegram.notify(
                    message='В данный момент база должна быть пуста', token=os.environ['TELEGRAM_KEY'],
                    chat_id=os.environ['TELEGRAM_CHAT_ID'])
                logger.debug('В данный момент база должна быть пуста')

                return new_pages_schema

            return []
        except Exception as e:
            return json.dumps({"error": e})

    # TODO: из JS-скрипта кидаю методы другой (delete)


class RemoveBookmarks(Resource):
    def __init__(self):
        self.bookmarks_for_remove_schema = BookmarksSchema(many=True)

    session: scoped_session = db.session

    def get(self):
        try:
            bookmarks_for_remove: list = BookmarksForRemove.query.all()

            if bookmarks_for_remove:
                bookmarks_for_remove = self.bookmarks_for_remove_schema.dump(bookmarks_for_remove)
                logger.info(f'Тип:{type(bookmarks_for_remove)}')
                logger.info(f'Закладки для удаления из базы: {bookmarks_for_remove}')

                telegram = get_notifier('telegram')
                telegram.notify(
                    message=f'Закладки для удаления из базы: {bookmarks_for_remove}', token=os.environ['TELEGRAM_KEY'],
                    chat_id=os.environ['TELEGRAM_CHAT_ID'])

                BookmarksForRemove.query.delete()
                db.session.commit()

                telegram.notify(
                    message='В данный момент база "bookmarks_for_remove" должна быть пуста',
                    token=os.environ['TELEGRAM_KEY'],
                    chat_id=os.environ['TELEGRAM_CHAT_ID'])
                logger.debug('В данный момент база "bookmarks_for_remove" должна быть пуста')
                return bookmarks_for_remove

            return []
        except Exception as e:
            return json.dumps({"error": e})
