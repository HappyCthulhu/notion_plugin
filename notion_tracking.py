import os
from datetime import datetime

import psycopg2 as psycopg2
from notifiers import get_notifier
from notion.block import PageBlock
from notion.client import NotionClient

from logging_settings import set_logger
# 3: заметка присутствует в списке notion-страниц, но отсутствует в закладках
from parse_bookmarks import parse_bookmarks


# TODO: проверяю ли я где-то перед добавлянием новой страницы в букмарки, нет ли ее в букмарках случаем?
# TODO: продумать, как это все поделить


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
        # TODO: сюда вообще нужно было добавлять last_edited_time, create_time?
        path.append({'title': block.title.lower(), 'page_url': block.get_browseable_url(),
                     'created_time': block._get_record_data()['created_time'],
                     'last_edited_time': block._get_record_data()['last_edited_time']})

    else:
        comparing_depth_to_length = compare_depth_to_length(depth)
        page_name, page_url = create_bookmark_data(comparing_depth_to_length, depth, block)

        path.append({'title': page_name, 'page_url': page_url, 'created_time': block._get_record_data()['created_time'],
                     'last_edited_time': block._get_record_data()['last_edited_time']})

        if not page_url in old_pages_links:
            logger.info(f'Найдена новая страница: {page_name}: {page_url}')

            telegram = get_notifier('telegram')
            telegram.notify(
                message=page_name, token=os.environ['TELEGRAM_KEY'], chat_id=os.environ['TELEGRAM_CHAT_ID'])

            new_pages.append({'title': page_name, 'page_url': page_url})

            created_time = datetime.fromtimestamp(float(str(block._get_record_data()['created_time'])[0:-3]))
            last_edited_time = datetime.fromtimestamp(float(str(block._get_record_data()['last_edited_time'])[0:-3]))

            cursor.execute(
                f"INSERT INTO new_pages (title, link, created_time, last_edited_time) VALUES ('{page_name}', '{page_url}', '{created_time}', '{last_edited_time}')")
            conn.commit()

            cursor.execute(
                f"INSERT INTO all_notion_pages (title, link, created_time, last_edited_time) VALUES ('{page_name}', '{page_url}', '{created_time}', '{last_edited_time}')")
            conn.commit()

            path.append(
                {'title': page_name, 'page_url': page_url, 'created_time': block._get_record_data()['created_time'],
                 'last_edited_time': block._get_record_data()['last_edited_time']})

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

    global conn, cursor

    conn, cursor = get_conn_and_cursor()

    cursor.execute(f"SELECT title, link, created_time, last_edited_time FROM all_notion_pages;")
    old_pages = [{'title': elem[0], 'page_url': elem[1]} for elem in cursor.fetchall()]

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


    for page in path:
        cursor.execute(
            f"INSERT INTO all_notion_pages (title, link, created_time, last_edited_time) VALUES ('{page['title']}', '{page['page_url']}', '{page._get_record_data()['created_time']}', '{page._get_record_data()['last_edited_time']}')")
    conn.commit()

    # TODO: возможно эту часть можно перенести выше, чтоб после обнаружения файлы перезапись шла сразу

    # TODO: wtf, где это использовалось
    exist_in_notion_but_not_in_chrome_bookmarks = compare_bookmarks_with_notion_pages(parse_bookmarks(), old_pages)

    conn.close()

    logger.debug('Finished tracking Notion')


# TODO: прихуярить инпуты
logger = set_logger()
