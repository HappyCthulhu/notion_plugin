import json
import os
import time

from notifiers import get_notifier

from logging_settings import set_logger
from parse_bookmarks import main


# 2: переименование заметки (перенос заметки в другое место) (url идентичен, меняется имя)
## удаляем заметку с этим url
## добавляем новую заметку

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
            telegram = get_notifier('telegram')
            telegram.notify(
                message=f'Были найдены дублированные закладки. Их idшники: {duplicates_ids[1:]}',
                token=os.environ['TELEGRAM_KEY'], chat_id=os.environ['TELEGRAM_CHAT_ID'])

            ids_for_removing.append(*duplicates_ids[1:])

    return ids_for_removing


def get_bookmarks_ids_of_deleted_pages(notion_pages, bookmarks):
    notion_pages_links = [notion_page['page_url'] for notion_page in notion_pages]
    deleted_pages = []

    for bookmark in bookmarks:
        if bookmark['page_url'] not in notion_pages_links:
            deleted_pages.append(bookmark)
            telegram = get_notifier('telegram')

            logger.debug(f"Найдена новая страница: {bookmark['title']}: {bookmark['page_url']}")
            from logging_settings import set_logger
            telegram.notify(
                message=f'Страница {bookmark["title"]} была удалена', token=os.environ['TELEGRAM_KEY'],
                chat_id=os.environ['TELEGRAM_CHAT_ID'])

    deleted_pages_ids = [bookmark['id'] for bookmark in deleted_pages]

    return deleted_pages_ids


while True:
    logger = set_logger()
    time.sleep(1)

    chrome_bookmarks = main()

    all_notion_pages_fp = 'all_notion_pages.json'
    pages_for_removing_fp = 'pages_for_removing.json'

    with open(all_notion_pages_fp, 'r') as all_pages_file:
        notion_pages = json.load(all_pages_file)

    # 1: если заметка была удалена в Notion: вся информация о закладке есть в браузере, но нет в списке страниц Notion)
    deleted_pages_ids = get_bookmarks_ids_of_deleted_pages(notion_pages, chrome_bookmarks)

    duplicated_bookmarks_ids = get_duplicated_bookmarks_ids(chrome_bookmarks)

    ids_for_removing = (*deleted_pages_ids, *duplicated_bookmarks_ids)

    with open(pages_for_removing_fp, 'w') as pages_for_removing_file:
        json.dump(ids_for_removing, pages_for_removing_file)

    logger.debug(
        'Ids notion pages for remove were dumped in file(bookmarks duplicates and bookmarks, which reference to deleted pages)')
