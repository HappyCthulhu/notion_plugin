import json
import os
from pathlib import Path

import psycopg2 as psycopg2
from notifiers import get_notifier
from notion.block import PageBlock
from notion.client import NotionClient

from logging_settings import set_logger
# 3: заметка присутствует в списке notion-страниц, но отсутствует в закладках
from parse_bookmarks import parse_bookmarks


# TODO: проверяю ли я где-то перед добавлянием новой страницы в букмарки, нет ли ее в букмарках случаем?


def get_conn_and_cursor():
    conn = psycopg2.connect(host=os.environ['DB_HOST_NAME'], user=os.environ['DB_USER_NAME'],
                            password=os.environ['DB_PASSWORD'], dbname=os.environ['DB_NAME'])
    cursor = conn.cursor()
    return conn, cursor


def get_childs(page):
    children_pages = page.children.filter(type=PageBlock)
    return children_pages


def compare_depth_to_length(depth):
    if len(path[-1]['title'].split("/")) < depth + 1:
        return 'depth_more_than_length'

    elif len(path[-1]['title'].split("/")) == depth + 1:
        return 'length_and_depth_are_equal'

    else:
        return 'length_more_than_depth'


def append_in_list(var, title, url):
    var.append({'title': title, 'url': url})


def create_bookmark_data(comparing_depth_to_length, depth, _block):
    _dict = {
        'depth_more_than_length': (f'{path[-1]["title"]}/{_block.title.lower()}', _block.get_browseable_url()),
        'length_and_depth_are_equal': (
            f"{'/'.join(path[-1]['title'].split('/')[0:-1])}/{_block.title.lower()}", _block.get_browseable_url()),
        'length_more_than_depth': (
            f"{'/'.join(path[-1]['title'].split('/')[0:depth])}/{_block.title.lower()}", _block.get_browseable_url())
    }

    bookmark = _dict[comparing_depth_to_length]

    return bookmark


def collect_pages(block, depth=0):
    if depth == 0:
        path.append({'title': block.title.lower(), 'page_url': block.get_browseable_url()})

    else:
        comparing_depth_to_length = compare_depth_to_length(depth)
        page_name, page_url = create_bookmark_data(comparing_depth_to_length, depth, block)

        path.append({'title': page_name, 'page_url': page_url})



        if not page_url in old_pages_links:
            logger.info(f'Найдена новая страница: {page_name}: {page_url}')

            telegram = get_notifier('telegram')
            telegram.notify(
                message=page_name, token=os.environ['TELEGRAM_KEY'], chat_id=os.environ['TELEGRAM_CHAT_ID'])

            new_pages.append({'title': page_name, 'page_url': page_url})

            cursor.execute(
                f"INSERT INTO new_pages (title, link) VALUES ('{page_name}', '{page_url}')")
            conn.commit()

            path.append({'title': page_name, 'page_url': page_url})


    for child in block.children:
        if child.type in ["page", "collection"]:
            collect_pages(child, depth=depth + 1)


def compare_bookmarks_with_notion_pages(bookmarks, notion_pages):
    notion_pages_to_add = []

    bookmarks_titles_urls = {bookmark['title']: bookmark['page_url'] for bookmark in bookmarks}

    for notion_page in notion_pages:
        if bookmarks_titles_urls.get(notion_page['title']) == notion_page['page_url']:
            continue
        else:
            notion_pages_to_add.append(notion_page)

    if notion_pages_to_add:
        for_logging = {bookmark["title"]: bookmark["page_url"] for bookmark in notion_pages_to_add}
        # TODO: везде приделать один message
        message = f'Найдены страницы Notion, не присутствующие в закладках: \n{for_logging}'
        logger.critical(message)

        telegram = get_notifier('telegram')
        telegram.notify(message=message, token=os.environ['TELEGRAM_KEY'], chat_id=os.environ['TELEGRAM_CHAT_ID'])

    return notion_pages_to_add


def notion_tracking():
    logger.debug('Starting tracking Notion')

    for file in (all_pages_file, new_pages_file):
        if not Path(file).is_file():
            with open(file, 'w') as file_data:
                json.dump({}, file_data)

    with open(all_pages_file, 'r') as file:
        old_pages = json.load(file)

    global conn, cursor

    conn, cursor = get_conn_and_cursor()


    # TODO: это точно норм работает?
    global old_pages_links
    old_pages_links = [page['page_url'] for page in old_pages]

    client = NotionClient(token_v2=os.environ.get('TOKEN'))
    link = os.environ['LINK']
    page = client.get_block(link)
    child_pages = get_childs(page)

    global path
    path = []

    global new_pages
    new_pages = []

    # TODO: корневые страницы не добавляются в Notion
    for block in child_pages:
        collect_pages(block)

    with open(all_pages_file, 'w') as file:
        json.dump(path, file, ensure_ascii=False, indent=4)

    cursor.execute(f'TRUNCATE TABLE all_notion_pages CASCADE')

    for page in path:
        cursor.execute(
            f"INSERT INTO all_notion_pages (title, link) VALUES ('{page['title']}', '{page['page_url']}')")
    conn.commit()

    # TODO: возможно эту часть можно перенести выше, чтоб после обнаружения файлы перезапись шла сразу
    with open(new_pages_file, 'r', encoding='utf-8') as file:
        file_data = json.load(file)

    exist_in_notion_but_not_in_chrome_bookmarks = compare_bookmarks_with_notion_pages(parse_bookmarks(), old_pages)

    with open(new_pages_file, 'w') as file:
        # TODO: это точно работает нормально? Написать юнит-тест
        # TODO: и вообще: все, что находится в этой функции нужно разбить по маленьким функциям
        if file_data:
            json.dump([*json.loads(file_data), *new_pages, *exist_in_notion_but_not_in_chrome_bookmarks], file,
                      ensure_ascii=False, indent=4)

        else:
            json.dump([*new_pages, *exist_in_notion_but_not_in_chrome_bookmarks], file, ensure_ascii=False, indent=4)

    conn.close()

    logger.debug('Finished tracking Notion')


# TODO: прихуярить инпуты
logger = set_logger()

all_pages_file = 'all_notion_pages.json'
new_pages_file = 'new_notion_pages.json'
