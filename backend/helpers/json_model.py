import os
from datetime import datetime
from backend.helpers.logger_settings import logger

import requests

from backend.models import db, AllNotionPages


class CACHEDPAGECHUNK:
    def __init__(self, page_id):

        self.page_id = page_id

        self.response = self.send_request()
        if self.response.status_code == 200:
            self.blocks = self.response.json()['recordMap']['block']
        else:
            logger.critical(f'Код ошибки: {self.response.status_code}')
            logger.critical(f'Текст ошибки: {self.response.text}')

        self.structure_pages()
        self.create_breadcrumbs()

    def send_request(self):

        json_payload = {
            'page': {
                'id': self.page_id,
            },
            'limit': 30,
            'cursor': {
                'stack': [],
            },
            'chunkNumber': 0,
            'verticalColumns': False,
        }

        response = requests.post(
            'https://www.notion.so/api/v3/loadCachedPageChunk',
            cookies=cookies,
            headers={'notion-client-version': '23.10.25.10', },
            json=json_payload
        )

        return response

    def check_if_block_is_valid_page(self, block_updates):
        if not block_updates.get('value'):
            # print('value doesnt exist')
            return False

        if not block_updates['value'].get('value'):
            # print('value doesnt exist')
            return False

        # проверять значение 'alive' необходимо именно конструкцией if some_key in obj.keys(), а то ключ-то может существовать, однако его значение может быть False
        if not 'alive' in block_updates['value']['value'].keys():
            # print('page is dead')
            return False

        if not block_updates['value']['value'].get('properties'):
            # print('properties doesnt exist')
            return False

        if not block_updates['value']['value'].get('parent_table'):
            # print('parent_table doesnt exist')
            return False

        if not block_updates['value'].get('role'):
            # print('role doesnt exist')
            return False

        if not block_updates['value']['value'].get('properties'):
            # print('title doesnt exist')
            return False

        if not block_updates['value']['value']['properties'].get('title'):
            # print('title doesnt exist')
            return False

        if block_updates['value']['value']['parent_id'] == self.page_id:
            # print(f'parent_id equal to searched page_id.  \nЭта страница ("{block_updates["value"]["value"]["properties"].get("title")}") является вложенной страницей той, для которой мы пытаемся сформировать breadcrumbs.')
            return False

        if not block_updates['value']['value'].get('type'):
            # print('type doesnt exist')
            return False

        if not block_updates['value']['role'] == 'editor':
            return False

        if not block_updates['value']['value']['type'] == 'page':
            # print(f'This block in not page. Its: {block_updates["value"]["value"]["type"]}')
            return False

        if not block_updates['value']['value']['parent_table'] == 'block' and not block_updates['value']['value'][
                                                                                      'parent_table'] == 'space':
            # print(
            #     f'Parent table of this page isn`t space or block. '
            #     f'Its: {block_updates["value"]["value"]["parent_table"]}')
            return False

        return True

    def structure_pages(self):
        self.structured_pages = []

        for block in self.blocks.values():
            if self.check_if_block_is_valid_page(block):
                self.structured_pages.append({'id': block['value']['value']['id'],
                                              'title': block['value']['value']['properties']['title'][0],
                                              'parent_id': block['value']['value']['parent_id'],
                                              'parent_table': block['value']['value']['parent_table']
                                              })
        return self.structured_pages

    def create_breadcrumbs(self):
        # формируем список страниц таким образом, чтоб root_page стоял на первом месте

        self.breadcrumbs_pages = self.structured_pages

        root_page = list(filter(lambda page: page['parent_table'] == 'space', self.breadcrumbs_pages))
        if root_page:
            self.breadcrumbs_pages.remove(root_page[0])
            self.breadcrumbs_pages.insert(0, root_page[0])

        for count, parent_page in enumerate(self.breadcrumbs_pages):
            child_page = list(filter(lambda x: x.get('parent_id') == parent_page['id'], self.breadcrumbs_pages))

            if not child_page:
                self.breadcrumbs_pages.pop(count)
                self.breadcrumbs_pages.append(parent_page)
                continue

            self.breadcrumbs_pages.remove(child_page[0])
            self.breadcrumbs_pages.insert(count + 1, child_page[0])

        # удаляем root_page ('Пространство') с помощью slice (не методом pop, потому что pop возвращает удаленный элемент!)
        self.breadcrumbs = '/'.join([page['title'][0] for page in self.breadcrumbs_pages][1:]).lower()

        return self.breadcrumbs


class ACTIVITYLOG:
    def __init__(self):

        space_id = self.get_spaceid()

        self.response = self.send_request(space_id)
        if self.response.status_code == 200:
            self.blocks = self.response.json()['recordMap']['block']
        else:
            logger.critical(f'Код ошибки: {self.response.status_code}')
            logger.critical(f'Текст ошибки: {self.response.text}')

        self.structure_page()
        self.get_last_edited_time_from_db()
        if self.last_edited_time:
            self.find_recently_changed_blocks()
        else:
            logger.debug('AllNotionPages db is empty')

    def get_spaceid(self):

        # TODO: стоит дампить его в переменные среды. И сделать проверку, есть ли в переменных среды space_id
        if os.environ.get('SPACE_ID'):
            return os.environ.get('SPACE_ID')
        else:
            response = requests.post(
                'https://www.notion.so/api/v3/getSpaces',
                cookies={'token_v2': os.environ['TOKEN']},
                headers={
                    'notion-client-version': '23.10.25.10',
                    'referer': os.environ['LINK']
                },
                json={}
            ).json()

            space_view = response[[*response][0]]['space_view']
            space_id = space_view[[*space_view][0]]['value']['value']['space_id']

            os.environ.get('SPACE_ID')

        return space_id

    def send_request(self, space_id):
        json_payload = {
            # TODO: вынести в переменные среды
            'spaceId': space_id,
            'limit': 100,
            'activityTypes': [],
        }

        response = requests.post('https://www.notion.so/api/v3/getActivityLog',
                                 cookies=cookies, json=json_payload)

        return response

    @staticmethod
    def check_if_block_is_valid_page(block_updates):
        # TODO: датамодел прихуярить??? как сделать так, чтоб было просто дебажить и не было кучи if`ов. Плюс еще чтоб return работал. nested obj в датамодел прошарить
        # проверять наличия ключа нужно именно конструкцией if some_key in obj.keys(), а то ключ-то может существовать, однако его значение может быть False
        if block_updates.get('role') and \
                block_updates.get('value') and \
                'alive' in block_updates['value'].keys() and \
                block_updates['value'].get('properties') and \
                block_updates['value'].get('parent_table') and \
                block_updates['value']['properties'].get('title') and \
                block_updates['value'].get('type'):

            if block_updates['role'] == 'editor' and \
                    block_updates['value']['type'] == 'page' and \
                    block_updates['value']['parent_table'] == 'block':
                return True

    @staticmethod
    def timestamp_to_datetime(timestamp):
        return datetime.fromtimestamp(float(str(timestamp)[0:-3]))

    @staticmethod
    def create_link_to_page(page_id):
        page_id_without_dash = page_id.replace('-', '')

        return f'https://www.notion.so/{page_id_without_dash}'

    def create_page_structure(self, block_updates):

        if self.check_if_block_is_valid_page(block_updates[1]):
            page = {'id': block_updates[0], 'link': self.create_link_to_page(block_updates[0]),
                    'alive': block_updates[1]['value']['alive'], 'parent_id': block_updates[1]['value']['parent_id'],
                    'created_time': self.timestamp_to_datetime(block_updates[1]['value']['created_time']),
                    'last_edited_time': self.timestamp_to_datetime(block_updates[1]['value']['last_edited_time']),
                    'title': block_updates[1]['value']['properties']['title'][0][0].lower()}

            if len(block_updates[1]['value']['properties']['title'][0]) > 0:
                # print(f"У блока несколько названий: {block_updates[1]['value']['value']['properties']['title']}")
                pass

            return page

    def structure_page(self):
        # можно получать бесконечное количество изменений, просто нужно использовать startingAfterId: "some_id"
        structured_pages = []

        for modified_page in self.blocks.items():
            structured_page = self.create_page_structure(modified_page)

            if structured_page:
                structured_pages.append(structured_page)

        self.structured_pages = structured_pages

    def get_last_edited_time_from_db(self):
        pages_from_db = db.session.query(AllNotionPages).all()
        if pages_from_db:
            latest_time = pages_from_db[0].last_edited_time

            for page in pages_from_db:
                if page.last_edited_time > latest_time:
                    latest_time = page.last_edited_time

            self.last_edited_time = latest_time
        else:
            self.last_edited_time = None

    def find_recently_changed_blocks(self):
        self.recently_changed_pages = []

        for block in self.structured_pages:
            if block:
                last_edited_time = block['last_edited_time']

                # если изменения в Notion были внесены практически одновременно, Notion ставит им один last_edited_time. Поэтому использую оператор "нестрого больше"
                if last_edited_time >= self.last_edited_time:
                    self.recently_changed_pages.append(block)

        return self.recently_changed_pages


cookies = {'token_v2': os.environ['TOKEN']}
