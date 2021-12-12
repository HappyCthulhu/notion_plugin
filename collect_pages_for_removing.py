import json
import os

import psycopg2
from notifiers import get_notifier

from logging_settings import set_logger
from parse_bookmarks import parse_bookmarks


# 2: переименование заметки (перенос заметки в другое место) (url идентичен, меняется имя)
## удаляем заметку с этим url
## добавляем новую заметку

# TODO: сделать одно соединение с ДБ для всех файлов
# TODO: написать тесты к этой всей красоте


def get_duplicated_bookmarks_ids(bookmarks):
    ids_for_removing = []

    for bookmark in bookmarks:
        if bookmark['id'] in ids_for_removing:
            continue

        duplicates = list(
            filter(lambda elem: elem['title'] == bookmark['title'] and elem['page_url'] == bookmark['page_url'],
                   bookmarks))

        # TODO: переделать в кортеж, если возможно
        duplicates_ids = [duplicate['id'] for duplicate in duplicates]
        if len(duplicates) > 1:
            telegram = get_notifier('telegram')
            telegram.notify(
                message=f'Были найдены дублированные закладки. Idшники для удаления: {duplicates_ids[1:]}\n'
                        f'Название закладки: {bookmark["title"]}\n'
                        f'Url закладки: {bookmark["page_url"]}',
                token=os.environ['TELEGRAM_KEY'], chat_id=os.environ['TELEGRAM_CHAT_ID'])

            logger.info(f'Были найдены дублированные закладки:\n'
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
            telegram = get_notifier('telegram')

            logger.debug(f"Страница была удалена из Notion: {bookmark['title']}: {bookmark['page_url']}")
            telegram.notify(
                message=f'Страница была удалена из Notion: "{bookmark["title"]}"', token=os.environ['TELEGRAM_KEY'],
                chat_id=os.environ['TELEGRAM_CHAT_ID'])

    deleted_pages_ids = [bookmark['id'] for bookmark in deleted_pages]

    return deleted_pages_ids


def get_conn_and_cursor():
    conn = psycopg2.connect(host=os.environ['DB_HOST_NAME'], user=os.environ['DB_USER_NAME'], password=os.environ['DB_PASSWORD'], dbname=os.environ['DB_NAME'])
    cursor = conn.cursor()
    return conn, cursor


def collect_pages_for_removing():
    conn, cursor = get_conn_and_cursor()

    cursor.execute(f"SELECT title, link FROM all_notion_pages;")

    notion_pages = [{'title': page[0], 'page_url': page[1]} for page in cursor.fetchall()]

    chrome_bookmarks = parse_bookmarks()

    # 1: если заметка была удалена в Notion: вся информация о закладке есть в браузере, но нет в списке страниц Notion)
    deleted_pages_ids = get_bookmarks_ids_of_deleted_pages(notion_pages, chrome_bookmarks)

    duplicated_bookmarks_ids = get_duplicated_bookmarks_ids(chrome_bookmarks)

    ids_for_removing = (*deleted_pages_ids, *duplicated_bookmarks_ids)

    for id in ids_for_removing:
        cursor.execute(
            f"INSERT INTO bookmarks_for_remove (bookmark_id) VALUES ('{id}')")
        conn.commit()

    logger.debug('Finished collecting pages for removing')


logger = set_logger()

# TODO: все это нужно удалить позже
all_notion_pages_fp = 'all_notion_pages.json'
pages_for_removing_fp = 'pages_for_removing.json'