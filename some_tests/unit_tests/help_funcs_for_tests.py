import time
from datetime import datetime

from app import db, app
from backend.helpers.parse_bookmarks import parse_bookmarks
from backend.models import AllNotionPages


def check_present_of_record_in_db_all_notion_pages(title):
    with app.app_context():
        if db.session.query(AllNotionPages).filter_by(title=title).all():
            return True
        else:
            return False


def find_bookmark_by_title(title):
    bookmarks = parse_bookmarks()
    for bookmark in bookmarks:
        if bookmark['title'] == title:
            return True

    return False


def wait_until(what, title, timeout, total_time):
    start_time = datetime.now()
    while int((datetime.now() - start_time).total_seconds()) < total_time:
        if what(title):
            return True
        time.sleep(timeout)

    return False


def wait_until_not(what, title, timeout, total_time):
    start_time = datetime.now()
    while int((datetime.now() - start_time).total_seconds()) < total_time:
        if what(title):
            time.sleep(timeout)
        else:
            return True

    return False
