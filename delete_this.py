import json
import os


def get_bookmarks_from_local_directory():
    print('Not via SSH')

    with open(JSONIN, "r", encoding='utf-8') as f:
        bookmarks = json.load(f)

        return bookmarks


JSONIN = os.environ['JSONIN']
print(get_bookmarks_from_local_directory())
