import time
from datetime import datetime

from app import db
from models import AllNotionPages
from parse_bookmarks import parse_bookmarks


def check_present_of_record_in_db_all_notion_pages(title):
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
