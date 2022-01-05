import time
from datetime import datetime

import allure
import pytest
from mimesis.random import Random

from app import db
from collect_pages_for_removing import get_bookmarks_ids_of_deleted_pages, get_duplicated_bookmarks_ids
from collect_pages_for_removing import logger
from models import AllNotionPages, NewNotionPages
from notion_tracking import notion_tracking
from parse_bookmarks import parse_bookmarks
from some_tests.unit_tests.test_data.test_data import BookmarksDontContainsFewNotionPages

rand = Random()


# TODO: все это чудо вынести в отдельные фаел
def find_bookmark_by_title(title):
    bookmarks = parse_bookmarks()
    for bookmark in bookmarks:
        if bookmark['title'] == title:
            return True

    return False


def wait_until(bookmark_title, timeout, total_time):
    start_time = datetime.now()
    while int((datetime.now() - start_time).total_seconds()) < total_time:
        if find_bookmark_by_title(bookmark_title):
            return True
        time.sleep(timeout)

    return False


def wait_until_not(bookmark_title, timeout, total_time):
    start_time = datetime.now()
    while int((datetime.now() - start_time).total_seconds()) < total_time:
        if find_bookmark_by_title(bookmark_title):
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
    def test_get_bookmarks_ids_of_deleted_pages(self):
        with allure.step("Получаем id  удаленных страниц"):
            ids_for_removing = get_bookmarks_ids_of_deleted_pages(BookmarksDontContainsFewNotionPages.notion_pages,
                                                                  BookmarksDontContainsFewNotionPages.parsed_bookmarks)

        with allure.step("Сравниваем id из функции с захардкоденными"):
            assert ids_for_removing == ["2782", "2783"]

    def test_get_duplicated_bookmarks_ids(self):
        ids_for_removing = get_duplicated_bookmarks_ids(BookmarksDontContainsFewNotionPages.duplicated_bookmarks)

        assert ids_for_removing == ["2789", "2790"]

    # TODO: можно написать тест с похожей структурой, только интеграционный: полную проверку цикла удаления
    # TODO: приделать неавтоматическую фикстуру, которая устанавливает connection с дб
    # @pytest.mark.debug
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
            assert wait_until(title, 0.1, 20), 'Тестовая закладка не была найдена'
            logger.debug('Тестовая запись добавлена в закладки')

        with allure.step('Проверяем, test_collect_pages_for_removing и  chrome-plugin удалил страницу из закладок'):
            assert wait_until_not(title, 0.1, 20), 'Тестовая закладка не была найдена'
            logger.debug('Тестовая запись была успешно удалена из закладок')


    @pytest.mark.skip
    @allure.title("Кейс удаленная notion-page: скрипт удаляет записи в БД, которых нет в Notion")
    def test_script_delete_record_about_non_existing_notion_page_from_db(self):
        with allure.step('Создаем тестовую запись в all_notion_pages'):
            time_ = datetime.now()
            page = AllNotionPages(title='test_page_in_all_notion_pages', link='https://test_page_al_notion.com', created_time=time_,
                                  last_edited_time=time_)

            db.session.add(page)
            db.session.add(page)
            db.session.commit()

        with allure.step('Проверяем, что она присутствует в БД'):
            test_shit = db.session.query(AllNotionPages).filter_by(title='test_page').all()
        with allure.step('Проверяем, что она пропала из БД'):
            test_shit = db.session.query(AllNotionPages).filter_by(title='test_page').all()
            assert not test_shit, 'Запись о несуществующей в Notion странице присутствует в БД. Сервер ее не удалил'

    # def test_notion_tracking(self):
    #     notion_tracking()
