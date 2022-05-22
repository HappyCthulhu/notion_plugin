from sqlalchemy import and_

from app import app
from backend.helpers.json_model import ACTIVITYLOG, CACHEDPAGECHUNK
from backend.helpers.logger_settings import logger
from backend.models import db, AllNotionPages, NewNotionPages


def not_changed_page(page):
    load_cached_page_chunk = CACHEDPAGECHUNK(page['id'])
    page_title = load_cached_page_chunk.breadcrumbs

    first_founded_page = db.session.query(AllNotionPages).filter(
        and_(AllNotionPages.title == page_title, AllNotionPages.link == page['link'])).first()

    if first_founded_page:
        first_founded_page.last_edited_time = page['last_edited_time']
        db.session.commit()

        return True


def new_page(page):
    load_cached_page_chunk = CACHEDPAGECHUNK(page['id'])
    page_title = load_cached_page_chunk.breadcrumbs

    exist_in_db = db.session.query(AllNotionPages).filter(
        AllNotionPages.link == page['link']).first()

    if not exist_in_db:
        created_time = page['created_time']
        last_edited_time = page['last_edited_time']

        logger.info(f'Страницы нет в AllNotionPages. Добавляю страницу: \n{page_title} | {page["link"]}')

        # TODO: потом раскомментить
        # telegram.notify(
        #     message=current_page['title'], token=os.environ['TELEGRAM_KEY'], chat_id=os.environ['TELEGRAM_CHAT_ID'])

        db.session.add(NewNotionPages(title=page_title, link=page['link'], created_time=created_time,
                                      last_edited_time=last_edited_time))
        db.session.commit()

        # TODO: попытаться таки это все перекинуть в views?
        db.session.add(AllNotionPages(title=page_title, link=page['link'], created_time=created_time,
                                      last_edited_time=last_edited_time))
        db.session.commit()

        return True


def renamed_page(page):
    load_cached_page_chunk = CACHEDPAGECHUNK(page['id'])
    page_title = load_cached_page_chunk.breadcrumbs
    # TODO: оно точно перестанет работать, если я all() на first() сменю, чтоб не дублировать строку?
    renamed_page = db.session.query(AllNotionPages).filter(and_(AllNotionPages.link == page['link'],
                                                                AllNotionPages.title != page_title)).first()

    if renamed_page:
        # this commit is needed, because link column consist unique values (script will try 2 push non-uniq value of renamed page without this commit)
        renamed_page.last_edited_time = page['last_edited_time']
        logger.debug(f'Страница "{renamed_page.title}" была переименована в "{page_title}"')
        renamed_page.title = page_title
        db.session.commit()
        return True


def delete_in_db_deleted_notion_page(page):
    exist_in_db = db.session.query(AllNotionPages).filter(AllNotionPages.link == page['link']).first()

    if exist_in_db:
        logger.debug(f'Страница была удалена из Notion. Удаляю из БД страницу: {page["title"]}')
        db.session.query(AllNotionPages).filter(AllNotionPages.link == page['link']).delete()
        db.session.commit()


def process_existing_in_notion_pages(pages):
    for page in pages:
        if not page['alive']:
            delete_in_db_deleted_notion_page(page)
            continue

        elif not_changed_page(page):
            continue
        # important order: first - renamed_page func, than new_page
        elif renamed_page(page):
            continue
        elif new_page(page):
            continue
        else:
            logger.critical(
                f'Some weird shit happened. Page is not renamed, changed or created... But u will find out very quick, i promise!\nPage Title: {page["title"]}')


# TODO: когда дойду до стадии запуска через celery, нужно будет app.context() удалить
with app.app_context():

    logger.debug('Start program')

    activity_log = ACTIVITYLOG()
    process_existing_in_notion_pages(activity_log.recently_changed_pages)

    logger.debug('End of program')