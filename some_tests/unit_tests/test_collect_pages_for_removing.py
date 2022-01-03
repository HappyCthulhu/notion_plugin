import time

import allure
import os
from datetime import datetime
from time import sleep

import pytest

from app import db
from collect_pages_for_removing import get_bookmarks_ids_of_deleted_pages, get_duplicated_bookmarks_ids, collect_pages_for_removing, get_conn_and_cursor
from models import AllNotionPages
from parse_bookmarks import parse_bookmarks
from some_tests.unit_tests.test_data.test_data import BookmarksDontContainsFewNotionPages

# TODO: создать классы, в которых будут содержаться данные для тестов (json-ны, например). Каждый аргумент класса (DataForTest.notion_page_was_deleted) должен возвращать bookmark, notion_pages с содажранием, соответствующим названию аргумента

# TODO: Может тестовые данные запихнуть в БД и создать правила их наполнения для conftest? фикстуры не обязательно должны применяться автоматически
# TODO: Notion-plugin. Сделать Selenium-скрипт, который добавлял бы заметку и ждал, пока она появится в ДБ. Тест должен выполняться последним

class TestCollectPagesForRemoving:
    @allure.id("5")
    @allure.title("Получение id  удаленных страниц")
    @allure.label("owner", "admin")
    def test_get_bookmarks_ids_of_deleted_pages(self):
        with allure.step("Получаем id  удаленных страниц"):
            ids_for_removing = get_bookmarks_ids_of_deleted_pages(BookmarksDontContainsFewNotionPages.notion_pages, BookmarksDontContainsFewNotionPages.parsed_bookmarks)

        with allure.step("Сравниваем id из функции с захардкоденными"):
            assert ids_for_removing == ["2782", "2783"]

    def test_get_duplicated_bookmarks_ids(self):
        ids_for_removing = get_duplicated_bookmarks_ids(BookmarksDontContainsFewNotionPages.duplicated_bookmarks)

        assert ids_for_removing == ["2789", "2790"]

    # TODO: можно написать тест с похожей структурой, только интеграционный: полную проверку цикла удаления
    # TODO: приделать неавтоматическую фикстуру, которая устанавливает connection с дб
    @allure.title("Скрипт удаляет закладку, которой нет в БД")
    def test_script_delete_bookmark_that_doesnt_exist_in_db(self):

        def get_test_bookmark_from_db(table_name):
            cursor.execute(
                f"SELECT title, link, created_time, last_edited_time FROM {table_name} WHERE link='%s';" % 'https://test_url.ru')
            return cursor.fetchall()



        with allure.step('Создаем тестовую запись в new_pages'):
            conn, cursor = get_conn_and_cursor()
            # Нужно добавить в new_pages, а не в all_notion_pages. В этом случае, страница будет добавлена в закладки, а не в all_notion_pages. В all_notion_pages скрипт добавляет, когда находит страницу при парсинге
            time_ = datetime.now()
            cursor.execute(
                "INSERT INTO new_pages (title, link, created_time, last_edited_time) VALUES ('test page', 'https://test_url.ru', '%s', '%s')" % (
                    time_, time_))
            conn.commit()

        # with allure.step('Ждем, когда flask добавит ее в "all_notion_pages"'):
        #     while get_test_bookmark_from_db('all_notion_pages'):
        #         sleep(1)

        # with allure.step('Удаляем запись из БД'):
        #     cursor.execute(
        #         "DELETE FROM all_notion_pages WHERE title='test page' AND link='https://test_url.ru'"
        #     )
        #     conn.commit()
        with allure.step('Ждем, пока отработает скрипт удаления страниц'):
            time.sleep(15)

        with allure.step('Проверяем, что заметка была успешно удалена скриптом'):
            bookmarks = parse_bookmarks()
            for bookmark in bookmarks:
                assert not bookmark['title'] == 'test page'
            # get_test_bookmark_from_db('bookmarks_for_remove')



    @pytest.mark.debug
    @allure.title("Кейс удаленная notion-page: скрипт удаляет записи в БД, которых нет в Notion")
    def test_script_delete_record_about_non_existing_notion_page_from_db(self):
        with allure.step('Создаем тестовую запись в all_notion_pages'):
            time_ = datetime.now()
            page = AllNotionPages(title='test_page', link='https://test_page.com', created_time=time_, last_edited_time=time_)
            db.session.add(page)
            db.session.commit()

        with allure.step('Проверяем, что она присутствует в БД'):
            test_shit = db.session.query(AllNotionPages).filter_by(title='test_page').all()
        with allure.step('Проверяем, что она пропала из БД'):
            test_shit = db.session.query(AllNotionPages).filter_by(title='test_page').all()
            assert not test_shit, 'Запись о несуществующей в Notion странице присутствует в БД. Сервер ее не удалил'


