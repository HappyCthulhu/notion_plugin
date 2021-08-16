import json
import os

# TODO: изменение названия или расположения файла
import time


def find_folder(tree, depth=0):
    for count, elem in enumerate(tree):
        if int(elem['id']) == folder_id:
            return elem

        else:

            if elem['type'] == 'url' or elem['id'] in folders_ids:
                continue

            elif elem['type'] == 'folder':
                folders_ids.append(elem['id'])

                path.append(f'{count} {elem["name"]}')
                depth = depth + 1
                debug = find_folder(elem['children'], depth)

                if debug:
                    return debug

        if len(path) == 1:
            path.clear()
            find_folder(first_stage, 0)

        else:
            new_path = path[0:depth - 1]
            path.clear()
            path.append(*new_path)

            for count in path:
                new_tree = first_stage[int(count.split()[0])]

            debug = find_folder(new_tree['children'], depth - 1)
            if debug:
                return debug


def main():
    folder_data = find_folder(first_stage)

    bookmarks = [{"title": children['name'], "page_url": children['url'], "id": children['id']} for children in
                 folder_data['children']]
    return bookmarks


time.sleep(1)
JSONIN = "/home/valera/.config/google-chrome/Default/Bookmarks"

with open(JSONIN, "r", encoding='utf-8') as f:
    Bookmarks = json.load(f)

folders_ids = []
folder_id = int(os.environ['BOOKMARKS_FOLDER'])

path = []
first_stage = Bookmarks['roots']['bookmark_bar']['children']
