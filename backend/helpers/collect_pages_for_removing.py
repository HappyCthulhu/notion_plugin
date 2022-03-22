import os
import time

from notifiers import get_notifier

from app import celery
from backend.models import BookmarksForRemove, AllNotionPages
from .logger_settings import logger
from .parse_bookmarks import parse_bookmarks
from ..models import db


def get_duplicated_bookmarks_ids(bookmarks):
    ids_for_removing = []

    for bookmark in bookmarks:
        if bookmark['id'] in ids_for_removing:
            continue

        duplicates = list(
            filter(lambda elem: elem['title'] == bookmark['title'] and elem['page_url'] == bookmark['page_url'],
                   bookmarks))

        duplicates_ids = [duplicate['id'] for duplicate in duplicates]
        if len(duplicates) > 1:
            # telegram = get_notifier('telegram')
            # telegram.notify(
            #     message=f'Были найдены дублированные закладки. Idшники для удаления: {duplicates_ids[1:]}\n'
            #             f'Название закладки: {bookmark["title"]}\n'
            #             f'Url закладки: {bookmark["page_url"]}',
            #     token=os.environ['TELEGRAM_KEY'], chat_id=os.environ['TELEGRAM_CHAT_ID'])

            logger.critical(f'Были найдены дублированные закладки:\n'
                            f'Idшники для удаления: {duplicates_ids[1:]}\n'
                            f'Название закладок: {bookmark["title"]}\n'
                            f'Url закладок: {bookmark["page_url"]}')

            ids_for_removing = [*ids_for_removing, *duplicates_ids[1:]]

    return ids_for_removing


def get_bookmarks_ids_of_deleted_pages(notion_pages, bookmarks):
    notion_pages_links = [notion_page['page_url'] for notion_page in notion_pages]
    deleted_pages = []

    for bookmark in bookmarks:
        if bookmark['page_url'] not in notion_pages_links:
            deleted_pages.append(bookmark)

            # TODO: логгирование существенно замедляет процесс. Необходимо сохранить логгирование, однако, сделать его единичным
            # telegram = get_notifier('telegram')

            # logger.debug(f"Страница была удалена из Notion: {bookmark['title']}: {bookmark['page_url']}")
            # telegram.notify(
            #     message=f'Страница была удалена из Notion: "{bookmark["title"]}"', token=os.environ['TELEGRAM_KEY'],
            #     chat_id=os.environ['TELEGRAM_CHAT_ID'])

    deleted_pages_ids = [bookmark['id'] for bookmark in deleted_pages]

    return deleted_pages_ids


@celery.task
def collect_pages_for_removing():
    notion_pages = [{'title': page.title, 'page_url': page.link} for page in db.session.query(AllNotionPages).all()]
    chrome_bookmarks = parse_bookmarks()

    # 1: если заметка была удалена в Notion: вся информация о закладке есть в браузере, но нет в списке страниц Notion)
    deleted_pages_ids = get_bookmarks_ids_of_deleted_pages(notion_pages, chrome_bookmarks)
    if deleted_pages_ids:
        logger.debug(f'Сейчас будет коммит в базу этих idшников: {deleted_pages_ids}')

    duplicated_bookmarks_ids = get_duplicated_bookmarks_ids(chrome_bookmarks)

    ids_for_removing = (*deleted_pages_ids, *duplicated_bookmarks_ids)

    for id in ids_for_removing:
        if db.session.query(BookmarksForRemove).filter(BookmarksForRemove.bookmark_id == id).all():
            time.sleep(20)
            logger.debug('Скрипт пытается запушить уже существующий в BookmarksForRemove idшник')
        if db.session.query(BookmarksForRemove).filter(BookmarksForRemove.bookmark_id == id).all():
            logger.critical(f'За 10 секунд idшник не удалился. Id: {id}')

        db.session.add(BookmarksForRemove(bookmark_id=id))
        db.session.commit()
