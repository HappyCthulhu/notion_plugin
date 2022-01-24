import json
import os

from notion.block import PageBlock

from collect_pages_for_removing import logger
from mimesis.random import Random
import allure
import pytest
from pathlib import Path

from notion.client import NotionClient

rand = Random()

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

@pytest.fixture(autouse=False, scope='session', name='client')
def get_notion_client():
    client = NotionClient(token_v2=os.environ.get('TOKEN'))
    yield client


@pytest.fixture(autouse=False, scope='function', name='title')
def title(client):
    title = rand.randstr(True, length=15)
    yield title


@pytest.fixture(autouse=False, scope='function', name='page')
def create_page_titles(client, title):
    with allure.step('Создаем запись в Notion'):
        page = client.get_block(os.environ['LINK'])
        new_page = page.children.add_new(PageBlock, title=title)
        logger.debug('Тестовая запись была создана в Notion')
        yield new_page

        new_page.remove()
