import os
import sys
import time
from datetime import datetime

import allure
import pytest
from mimesis.random import Random
from notion.block import PageBlock
from notion.client import NotionClient
from requests import HTTPError

from app import db
from collect_pages_for_removing import get_bookmarks_ids_of_deleted_pages, get_duplicated_bookmarks_ids
from collect_pages_for_removing import logger
from models import AllNotionPages, NewNotionPages
from parse_bookmarks import parse_bookmarks
from some_tests.unit_tests.test_data.test_data import BookmarksDontContainsFewNotionPages

rand = Random()


# TODO: все это чудо вынести в отдельные фаел
def check_present_of_record_in_db_all_notion_pages(title):
    # TODO: удалить переменную
    test = db.session.query(AllNotionPages).filter_by(title=title).all()

    if test:
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


# TODO: создать классы, в которых будут содержаться данные для тестов (json-ны, например). Каждый аргумент класса (DataForTest.notion_page_was_deleted) должен возвращать bookmark, notion_pages с содажранием, соответствующим названию аргумента

# TODO: Может тестовые данные запихнуть в БД и создать правила их наполнения для conftest? фикстуры не обязательно должны применяться автоматически
# TODO: Notion-plugin. Сделать Selenium-скрипт, который добавлял бы заметку и ждал, пока она появится в ДБ. Тест должен выполняться последним

class TestCollectPagesForRemoving:
    @allure.id("5")
    @allure.title("Получение id  удаленных страниц")
    @allure.label("owner", "admin")
    # TODO: dот этот тест переделать под БД
    def test_get_bookmarks_ids_of_deleted_pages(self):
        with allure.step("Получаем id  удаленных страниц"):
            ids_for_removing = get_bookmarks_ids_of_deleted_pages(BookmarksDontContainsFewNotionPages.notion_pages,
                                                                  BookmarksDontContainsFewNotionPages.parsed_bookmarks)

        with allure.step("Сравниваем id из функции с захардкоденными"):
            assert ids_for_removing == ["2782", "2783"]

    # TODO: dот этот тест переделать под БД
    def test_get_duplicated_bookmarks_ids(self):
        ids_for_removing = get_duplicated_bookmarks_ids(BookmarksDontContainsFewNotionPages.duplicated_bookmarks)

        assert ids_for_removing == ["2789", "2790"]

    # TODO: можно написать тест с похожей структурой, только интеграционный: полную проверку цикла удаления
    # TODO: приделать неавтоматическую фикстуру, которая устанавливает connection с дб
    @allure.title("Скрипт удаляет закладку, которой нет в БД")
    def test_script_delete_bookmark_that_doesnt_exist_in_db(self):
        with allure.step('Создаем тестовую запись в new_pages'):
            time_ = datetime.now()
            title = rand.randstr(True, length=15)
            link = f'https://{rand.randstr(True, length=15)}.com'

            db.session.add(NewNotionPages(title=title, link=link, created_time=time_, last_edited_time=time_))
            db.session.commit()

        with allure.step('Проверяем, что заметка присутствует в таблице'):
            result = db.session.query(NewNotionPages).filter_by(link=link).all()
            assert result
            logger.debug('Запись добавлена в таблицу new_pages')

        with allure.step('Проверяем, что chrome-plugin добавил страницу в закладки'):
            assert wait_until(find_bookmark_by_title, title, 0.1, 20), 'Тестовая закладка не была найдена'
            logger.debug('Тестовая запись добавлена в закладки')

        with allure.step('Проверяем, test_collect_pages_for_removing и  chrome-plugin удалил страницу из закладок'):
            assert wait_until_not(find_bookmark_by_title, title, 0.1, 20), 'Тестовая закладка не была найдена'
            logger.debug('Тестовая запись была успешно удалена из закладок')

    @allure.title("Кейс удаленная notion-page: скрипт удаляет записи в БД, которых нет в Notion")
    def test_script_delete_record_about_non_existing_notion_page_from_db(self):
        with allure.step('Создаем тестовую запись в all_notion_pages'):
            time_ = datetime.now()
            title = rand.randstr(True, length=15)
            link = f'https://{rand.randstr(True, length=15)}.com'
            db.session.add(AllNotionPages(title=title, link=link,
                                          created_time=time_, last_edited_time=time_))
            logger.debug(f'title: {title}')
            logger.debug(f'link: {link}')
            db.session.commit()

        with allure.step('Проверяем, что она присутствует в БД'):
            assert db.session.query(AllNotionPages).filter_by(title=title).all()
            logger.debug('Тестовая запись добавлена в all_notion_pages')

        with allure.step('Проверяем, что она пропала из БД'):
            assert wait_until(check_present_of_record_in_db_all_notion_pages, title, 1, 20)
            logger.debug('Тестовая запись присутствует в all_notion_pages')

        with allure.step('Проверяем, test_collect_pages_for_removing и  chrome-plugin удалил страницу из закладок'):
            assert wait_until_not(check_present_of_record_in_db_all_notion_pages, title, 1,
                                  600), 'Тестовая закладка не была найдена'
            logger.debug('Тестовая запись была успешно удалена из all_notion_pages')

    @pytest.mark.debug
    @allure.title("Проверка удаления страницы")
    def test_script_delete_from_db_deleted_in_notion_page(self):

        with allure.step('Устанавливаем connection c Notion'):
            # TODO: cделать тест коннекшена отдельным
            try:
                client = NotionClient(token_v2=os.environ.get('TOKEN'))

            except HTTPError:
                logger.critical('Wrong notion token')
                sys.exit()

        with allure.step('Создаем запись в Notion'):
            title = rand.randstr(True, length=15)
            page = client.get_block('https://www.notion.so/gazarov/0fe33ef038ba4ba489e4c6ab9b6430ee')
            new_page = page.children.add_new(PageBlock, title=title)
            logger.debug('Тестовая запись была создана в Notion')

        with allure.step('Ждем, пока она появится в all_notion_pages'):
            wait_until(find_bookmark_by_title, title, 0.1, 600), 'Тестовая закладка не была найдена'
            logger.debug('Тестовая запись присутствует в all_notion_pages')

        with allure.step('Удаляем созданную запись в Notion'):
            new_page_link = new_page.get_browseable_url()
            page = client.get_block(new_page_link)
            page.remove()

        with allure.step('Ждем, пока удалится из all_notion_pages'):
            logger.debug('Ждем удаления тестовой запсии из all_notion_page')
            assert wait_until_not(check_present_of_record_in_db_all_notion_pages, title, 1,
                                  600), 'Тестовая закладка не была найдена'

# TODO: cделать тест на проверку создания страницы
# TODO: написать тест, который с помощью селениума добавлял бы новую закладку с фиксированным названием, проверял, что она добавляется в Notion и удалял ее позже
# TODO: cделать тест на удаление переименованных страниц
# TODO: найти и заменить все токены и прочие штуки, которые должны быть заменены на переменные среды
