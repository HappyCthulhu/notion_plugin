import json

import pytest
from pathlib import Path

@pytest.fixture(autouse=True, scope='function', name='bookmarks')
def get_bookmarks():
    print(Path('.').absolute())
    with open(Path('.', 'some_tests', 'unit_tests', 'test_data', 'parsed_bookmarks.json').absolute(), 'r') as file:
        bookmarks = json.load(file)

        yield bookmarks


@pytest.fixture(autouse=True, scope='function', name='notion_pages')
def get_notion_pages():
    print(Path('.').absolute())
    with open(Path('.', 'some_tests', 'unit_tests', 'test_data', 'notion_pages.json').absolute(), 'r') as file:
        notion_pages = json.load(file)

        yield notion_pages
