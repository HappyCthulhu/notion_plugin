import os
from datetime import datetime

import psycopg2 as psycopg2
from notifiers import get_notifier
from notion.block import PageBlock
from notion.client import NotionClient
from sqlalchemy import and_

from app import db
from collect_pages_for_removing import logger
from models import AllNotionPages, NewNotionPages
from parse_bookmarks import parse_bookmarks


# TODO: проверяю ли я где-то перед добавлянием новой страницы в букмарки, нет ли ее в букмарках случаем?
# TODO: продумать, как это все поделить

# 3: заметка присутствует в списке notion-страниц, но отсутствует в закладках

def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(float(str(timestamp)[0:-3]))


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


def delete_in_db_deleted_notion_pages(all_current_pages):
    # в БД есть запись с таким же url, но другим названием: удаляем из БД, добавляем новую запись
    # БД содержит название и url заметки, которой нет в Notion: удаляем из БД
    current_pages_links = [page_from_db['page_url'] for page_from_db in all_current_pages]
    for old_link in old_pages_links:

        # БД содержит url заметки, котоой нет в notion
        if old_link not in current_pages_links:
            logger.debug(f'Найдена запись в all_notion_pages, url которой нет Notion. Удаляю из БД: {old_link}')
            db.session.commit()


# TODO: допилить
def delete_pages_that_been_renamed_and_duplicates_in_bd():
    all_notion_pages = AllNotionPages.query.all()
    for page in all_notion_pages:

        found_pages = db.session.query(AllNotionPages).filter_by(link=page.link).all()

        if len(found_pages) > 1:
            # первым значением делаем время, которое точно раньше любое моей созданной в Notion заметки
            latest_edited_time = datetime.strptime("2010-01-31", "%Y-%m-%d")
            for duplicate_page in found_pages:
                if latest_edited_time < duplicate_page.last_edited_time:
                    latest_edited_time = duplicate_page.last_edited_time

            db.session.query(AllNotionPages).filter(and_(AllNotionPages.link == page.link,
                                                         AllNotionPages.last_edited_time != latest_edited_time)).delete()
            db.session.commit()


def collect_pages(block, depth=0):
    if depth == 0:
        path.append({'title': block.title.lower(), 'page_url': block.get_browseable_url(),
                     'created_time': timestamp_to_datetime(block._get_record_data()['created_time']),
                     'last_edited_time': timestamp_to_datetime(block._get_record_data()['last_edited_time'])})

    else:
        comparing_depth_to_length = compare_depth_to_length(depth)
        page_name, page_url = create_bookmark_data(comparing_depth_to_length, depth, block)

        path.append({'title': page_name, 'page_url': page_url,
                     'created_time': timestamp_to_datetime(block._get_record_data()['created_time']),
                     'last_edited_time': timestamp_to_datetime(block._get_record_data()['last_edited_time'])})

    for child in block.children:
        if child.type in ["page", "collection"]:
            collect_pages(child, depth=depth + 1)


def add_pages_that_exist_in_notion_but_not_in_chrome_bookmarks(bookmarks, notion_pages):
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

        telegram.notify(message=message, token=os.environ['TELEGRAM_KEY'], chat_id=os.environ['TELEGRAM_CHAT_ID'])

        for page in notion_pages_to_add:
            db.session.add(NewNotionPages(title=page['title'], link=page['page_url'],
                                          created_time=page['created_time'], last_edited_time=page['last_edited_time']))
            db.session.commit()


def process_new_renamed_and_existed_pages(path):
    for current_page in path:

        # delete renamed_pages
        # TODO: эта строка чисто для дебага нужна. Удалить:
        delete_me = db.session.query(AllNotionPages).filter(
            and_(AllNotionPages.link == current_page['page_url'], AllNotionPages.title != current_page['title'])).all()
        result = db.session.query(AllNotionPages).filter(and_(AllNotionPages.link == current_page['page_url'],
                                                              AllNotionPages.title != current_page['title'])).delete()

        page_with_same_title_and_link_exist_in_db = db.session.query(AllNotionPages).filter(
            and_(AllNotionPages.link == current_page['page_url'], AllNotionPages.title == current_page['title'])).all()

        if not page_with_same_title_and_link_exist_in_db:
            # if not current_page['page_url'] in old_pages_links:
            title = current_page['title']
            link = current_page['page_url']
            created_time = current_page['created_time']
            last_edited_time = current_page['last_edited_time']

            telegram.notify(
                message=current_page['title'], token=os.environ['TELEGRAM_KEY'], chat_id=os.environ['TELEGRAM_CHAT_ID'])
            new_pages.append({'title': title, 'page_url': link})
            page = NewNotionPages(title=title, link=link, created_time=created_time,
                                  last_edited_time=last_edited_time)
            db.session.add(page)
            db.session.commit()

            page = AllNotionPages(title=title, link=link, created_time=created_time,
                                  last_edited_time=last_edited_time)
            db.session.add(page)
            # TODO: повторения этого удалить:

        else:
            # if page with exact link and title exist in db, we just change last_edited_time
            test = db.session.query(AllNotionPages).filter(and_(AllNotionPages.link == current_page['page_url'],
                                                                AllNotionPages.title == current_page['title'])).first()
            test.last_edited_time = current_page['last_edited_time']
            # TODO: здесь должна располагаться проверка на переименование? Типа, link есть, но title отличается
        db.session.commit()


def notion_tracking():
    logger.debug('Start tracking Notion')

    global conn, cursor

    conn, cursor = get_conn_and_cursor()

    # TODO: переделать
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



    # for page in path:
        # TODO: вспомнить и закомментировать, нахера это вообще нужно
        # TODO: корневые страницы все равно не индексируются (их нет в закладках в результате)(((
        # try:
        # TODO: крч трабл в том, что я у словаря пытаюсь метод notion-page вызвать

        # db.session.add(AllNotionPages(title=page['title'], link=page['page_url'], created_time=page['created_time'],
        #                               last_edited_time=page['last_edited_time']))
        # db.session.commit()

    # TODO: есть ощущение, что скрипт добавляет страницы, которые уже есть в БД
    process_new_renamed_and_existed_pages(path)
    # TODO: возможно эту часть можно перенести выше, чтоб после обнаружения файлы перезапись шла сразу

    # TODO: wtf, где это использовалось. Нужно это добавить в new_pages?
    delete_in_db_deleted_notion_pages(path)
    # TODO: раскомментить, когда найду причину повторного добавления закладок
    add_pages_that_exist_in_notion_but_not_in_chrome_bookmarks(parse_bookmarks(), path)

    # TODO: вообще, эта функция не нужна будет, если я сделаю правильный алгоритм всего. Скорее нужно тест написать, который отсутствие дубликатов в базе проверял
    delete_pages_that_been_renamed_and_duplicates_in_bd()
    logger.debug('Finished tracking Notion')


# TODO: не стоит ли подтягивать в ДБ all_notion_pages те страницы, что были найдены в дб new_pages? А то сейчас это иначе происходит
# TODO: прихуярить инпуты
telegram = get_notifier('telegram')
notion_tracking()
# TODO: почему в дб создаются дупликаты?