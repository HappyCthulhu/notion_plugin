import time

from app import celery
from backend.helpers.logger_settings import logger
from backend.helpers.parse_bookmarks import parse_bookmarks
from backend.models import BookmarksForRemove, AllNotionPages
from backend.models import db


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
    else:
        logger.debug(f'Закончен сбор. Закладок для удаления нету')

    duplicated_bookmarks_ids = get_duplicated_bookmarks_ids(chrome_bookmarks)

    ids_for_removing = (*deleted_pages_ids, *duplicated_bookmarks_ids)

    # TODO: проверить, нужно ли это вообще
    for id_ in ids_for_removing:
        if db.session.query(BookmarksForRemove).filter(BookmarksForRemove.bookmark_id == id_).all():
            time_count = 30
            logger.debug(f'Скрипт пытается запушить уже существующий в BookmarksForRemove idшник. Ждем {time_count} cекунд')
            time.sleep(time_count)
        if db.session.query(BookmarksForRemove).filter(BookmarksForRemove.bookmark_id == id_).all():
            logger.critical(f'За 30 секунд idшник не удалился. Id: {id_}')

        db.session.add(BookmarksForRemove(bookmark_id=id_))
        db.session.commit()
