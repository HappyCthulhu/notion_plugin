import allure
import os
from datetime import datetime
from time import sleep

import pytest

from collect_pages_for_removing import get_bookmarks_ids_of_deleted_pages, get_duplicated_bookmarks_ids, collect_pages_for_removing, get_conn_and_cursor
from parse_bookmarks import parse_bookmarks
from some_tests.unit_tests.test_data.test_data import BookmarksDontContainsFewNotionPages

# TODO: создать классы, в которых будут содержаться данные для тестов (json-ны, например). Каждый аргумент класса (DataForTest.notion_page_was_deleted) должен возвращать bookmark, notion_pages с содажранием, соответствующим названию аргумента

# TODO: Может тестовые данные запихнуть в БД и создать правила их наполнения для conftest? фикстуры не обязательно должны применяться автоматически

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
    @pytest.mark.debug
    def test_collect_pages_for_removing(self):
        def get_test_bookmark_from_db():
            cursor.execute(
                f"SELECT title, link, created_time, last_edited_time FROM new_pages WHERE link='%s';" % 'https://test_url.ru')
            return cursor.fetchall()

        # host = os.environ['DB_HOST_NAME']
        # user = os.environ['DB_USER_NAME']
        # password = os.environ['DB_PASSWORD']
        # dbname = os.environ['DB_NAME']

        conn, cursor = get_conn_and_cursor()

        time_ = datetime.now()

        cursor.execute(
            "INSERT INTO new_pages (title, link, created_time, last_edited_time) VALUES ('test page', 'https://test_url.ru', '%s', '%s')" % (
                time_, time_))

        conn.commit()

        while get_test_bookmark_from_db():
            sleep(1)


        cursor.execute(
            "DELETE FROM all_notion_pages WHERE title='test page' AND link='https://test_url.ru'"
        )
        conn.commit()

        bookmarks = parse_bookmarks()

        for bookmark in bookmarks:
            assert not bookmark['title'] == 'test'



