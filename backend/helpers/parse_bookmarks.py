import json
import os
import sys

import paramiko

from backend.helpers.logger_settings import logger


def get_bookmarks_from_local_directory():
    with open(JSONIN, "r", encoding='utf-8') as f:
        bookmarks = json.load(f)

    return bookmarks


def get_bookmarks_via_ssh():

    host, port, username, password, command = os.environ['SSH_HOST'], int(os.environ['SSH_PORT']), os.environ[
        'SSH_USERNAME'], os.environ['SSH_PASSWORD'], os.environ['SSH_COMMAND']
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port, username, password)

    stdin, stdout, stderr = ssh.exec_command(command)
    bookmarks = json.loads(''.join(stdout.readlines()))

    return bookmarks


# TODO: это может хреново работать, ибо должно вызываться всего раз за отработку цикл
def find_folder(tree, depth=0):
    for count, elem in enumerate(tree):

        # первый if/else работает с depth=0. С минимальной, корневой вложенностью
        # если нашли папку с закладками notion - возвращаем ее содержимое
        if int(elem['id']) == folder_id:
            return elem

        # если это не notion-папка
        else:
            # если это ссылка или элемент, присутствующий в folders_ids (то есть, уже натыкались на него раньше) - пропускаем
            if elem['type'] == 'url' or elem['id'] in folders_ids:
                continue

            # если это папка - добавляем в path строку типа id folder_name, добавляем глубину
            elif elem['type'] == 'folder':
                folders_ids.append(elem['id'])

                path.append(f'{count} {elem["name"]}')
                depth = depth + 1

                # TODO: не очень понятно, зачем это нужно, не удалось найти usercase
                debug = find_folder(elem['children'], depth)

                if debug:
                    return debug

        # если уровень вложенности - 1. Очищаем path и продолжаем поиск (ибо вложенности нет и можем возвращаться к нулевому - корневому уровню)
        if len(path) == 1:
            path.clear()

            find_folder(first_stage, 0)

        # если уровень вложенности больше 1
        else:
            new_path = path[0:depth - 1]
            path.clear()
            path.append(*new_path)

            for count in path:
                new_tree = first_stage[int(count.split()[0])]

            debug = find_folder(new_tree['children'], depth - 1)
            if debug:
                return debug


def parse_bookmarks():
    if os.environ['VIA_SSH'] == 'False':
        bookmarks = get_bookmarks_from_local_directory()

    elif os.environ['VIA_SSH'] == 'True':
        bookmarks = get_bookmarks_via_ssh()

    else:
        logger.critical('VIA_SHH env var is not set properly')
        sys.exit()

    global first_stage
    first_stage = bookmarks['roots']['bookmark_bar']['children']
    folder_data = find_folder(first_stage)

    try:
        bookmarks = [{"title": children['name'], "page_url": children.get('url'), "id": children['id']} for children in
                     folder_data['children'] if children.get('url')]

        return bookmarks

    except TypeError as e:
        logger.critical('Возможно, ты неправильно указал id папки с закладками в переменных среды')
        logger.debug(f'"error": {e}')


JSONIN = os.environ['JSONIN']

folders_ids = []
folder_id = int(os.environ['BOOKMARKS_FOLDER'])

path = []
