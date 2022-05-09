import json
import os
from pathlib import Path

import allure
import pytest
from mimesis.random import Random
from notion.block import PageBlock
from notion.client import NotionClient

from backend.helpers.collect_pages_for_removing import logger

rand = Random()


@pytest.fixture(autouse=False, scope='function', name='bookmarks')
def get_bookmarks():
    print(Path('.').absolute())
    with open(Path('.', 'some_tests', 'unit_tests', 'test_data', 'parsed_bookmarks.json').absolute(), 'r') as file:
        bookmarks = json.load(file)

        yield bookmarks


@pytest.fixture(autouse=False, scope='function', name='notion_pages')
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
        logger.debug(f'Создана новая страница. Название: {title}')
        yield new_page

        new_page.remove()
