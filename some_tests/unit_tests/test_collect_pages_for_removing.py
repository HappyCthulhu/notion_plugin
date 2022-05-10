import os
from datetime import datetime

import allure
from mimesis.random import Random
from notion.block import PageBlock
from notion.client import NotionClient
from sqlalchemy.orm import scoped_session

from app import db, app
from backend.helpers.logger_settings import logger
from backend.models import AllNotionPages, NewNotionPages
from some_tests.unit_tests.help_funcs_for_tests import wait_until, wait_until_not, find_bookmark_by_title, \
    check_present_of_record_in_db_all_notion_pages

# from some_tests.unit_tests.test_data.test_data import BookmarksDontContainsFewNotionPages

rand = Random()


# TODO: тест проверки обновления даты существующей записи
# TODO: сделать интеграционный тест для дублирования закладок
# TODO: создать классы, в которых будут содержаться данные для тестов (json-ны, например). Каждый аргумент класса (DataForTest.notion_page_was_deleted) должен возвращать bookmark, notion_pages с содажранием, соответствующим названию аргумента
# TODO: создать миграции для БД
# TODO: Может тестовые данные запихнуть в БД и создать правила их наполнения для conftest? фикстуры не обязательно должны применяться автоматически

class TestCollectPagesForRemoving:
    session: scoped_session = db.session

    @allure.title("Проверка наличия connection")
    def test_notion_connection(self):
        with allure.step('Устанавливаем connection c Notion'):
            client = NotionClient(token_v2=os.environ.get('TOKEN'))
            page = client.get_block(os.environ['LINK'])
            assert page

    # @allure.id("5")
    # @allure.title("Получение id  удаленных страниц")
    # @allure.label("owner", "admin")
    # TODO: dот этот тест переделать под БД
    # def test_get_bookmarks_ids_of_deleted_pages(self):
    # with allure.step("Получаем id  удаленных страниц"):
    #     ids_for_removing = get_bookmarks_ids_of_deleted_pages(BookmarksDontContainsFewNotionPages.notion_pages,
    #                                                           BookmarksDontContainsFewNotionPages.parsed_bookmarks)

    # with allure.step("Сравниваем id из функции с захардкоденными"):
    #     assert ids_for_removing == ["2782", "2783"]

    # TODO: dот этот тест переделать под БД
    # def test_get_duplicated_bookmarks_ids(self):
    # ids_for_removing = get_duplicated_bookmarks_ids(BookmarksDontContainsFewNotionPages.duplicated_bookmarks)
    #
    # assert ids_for_removing == ["2789", "2790"]

    # TODO: приделать неавтоматическую фикстуру, которая устанавливает connection с дб
    @allure.title("Скрипт удаляет закладку, которой нет в БД")
    def test_script_delete_bookmark_that_doesnt_exist_in_db(self, title):
        with allure.step('Создаем тестовую запись в new_pages'):
            time_ = datetime.now()
            link = f'https://{rand.randstr(True, length=15)}.com'

            # TODO: можно ли каким-то образом избавиться от app.app_context?
            with app.app_context():
                db.session.add(NewNotionPages(title=title, link=link, created_time=time_, last_edited_time=time_))
                db.session.commit()

        with allure.step('Проверяем, что заметка присутствует в таблице'):
            with app.app_context():
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
    def test_script_delete_record_about_non_existing_notion_page_from_db(self, title):
        with allure.step('Создаем тестовую запись в all_notion_pages'):
            time_ = datetime.now()
            link = f'https://{rand.randstr(True, length=15)}.com'
            with app.app_context():
                db.session.add(AllNotionPages(title=title, link=link,
                                              created_time=time_, last_edited_time=time_))
                db.session.commit()
                logger.debug(f'title: {title}')
                logger.debug(f'link: {link}')

        with allure.step('Проверяем, что она присутствует в БД'):
            with app.app_context():
                assert db.session.query(AllNotionPages).filter_by(title=title).all()
            logger.debug('Тестовая запись добавлена в all_notion_pages')

        with allure.step('Проверяем, что она пропала из БД'):
            assert wait_until(check_present_of_record_in_db_all_notion_pages, title, 1, 20)
            logger.debug('Тестовая запись присутствует в all_notion_pages')

        with allure.step('Проверяем, test_collect_pages_for_removing и  chrome-plugin удалил страницу из закладок'):
            assert wait_until_not(check_present_of_record_in_db_all_notion_pages, title, 1,
                                  600), 'Тестовая закладка не была найдена'
            logger.debug('Тестовая запись была успешно удалена из all_notion_pages')

    @allure.title("Проверка удаления страницы")
    def test_script_delete_from_db_deleted_in_notion_page(self, client, title):
        with allure.step('Создаем запись в Notion'):
            page = client.get_block(os.environ['LINK'])
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
            logger.debug('Ждем удаления тестовой записи из all_notion_page')
            assert wait_until_not(check_present_of_record_in_db_all_notion_pages, title, 1,
                                  600), 'Тестовая страница не была найдена в БД'

    @allure.title("Создание новой страницы")
    def test_script_catch_new_page(self, title, page, client):
        with allure.step('Ждем, пока она появится в all_notion_pages'):
            assert wait_until(find_bookmark_by_title, title, 0.1, 600), 'Тестовая страница не была найдена'

    @allure.title("Переименование страницы")
    def test_script_catch_renamed_page(self, title, page, client):
        with allure.step('Ждем, пока она появится в all_notion_pages'):
            wait_until(find_bookmark_by_title, title, 0.1, 600), 'Тестовая страница не была найдена'
            logger.debug('Тестовая запись присутствует в all_notion_pages')

        with allure.step('Переименовываем страницу'):
            new_page_link = page.get_browseable_url()
            page = client.get_block(new_page_link)
            new_title = rand.randstr(True, length=15)
            page.title = new_title

        with allure.step('Ждем, пока переименованная запись появится в all_notion_pages'):
            logger.debug('Ждем появления тестовой записи в all_notion_page')
            assert wait_until(check_present_of_record_in_db_all_notion_pages, new_title, 1,
                              600), 'Переименованная тестовая страница не была найдена в БД'

    def test_than_bookmarks_and_db_have_equal_count_of_records(self):
        with allure.step('Считаем количество notion-закладок в Chrome'):
            from backend.helpers.parse_bookmarks import parse_bookmarks
            count_of_bookmarks = len(parse_bookmarks())
        logger.debug(f'Количество закладок: {count_of_bookmarks}')

        with allure.step('Считаем количество записей в таблице all_notion_pages'):
            with app.app_context():
                count_of_db_records = len(db.session.query(AllNotionPages).all())
        logger.debug(f'Количество записей в таблице all_notion_pages: {count_of_db_records}')

        assert count_of_bookmarks == count_of_db_records, 'количество закладок и записей в таблице all_notion_pages не совпадают'


