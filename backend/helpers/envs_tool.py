# input()
# ask for root dir (manual adding or current directory - PWD)
# question, what type of files should we create (.env, .envrc, pytest.ini)
# search for all usage of os.enviropment or os.enviropment.get. get all used env vars
# if pytest.ini: dirs to place pytest.ini
## check, if this dir exist
# check if envs files already exists in all child-root directories. if no - create new file if yes - supplement them with new vars
# function, that create file of specific type
# input env: value, skip

import subprocess

from pathlib import Path


def define_root_dir():
    print(
        'Please, define root dir of your project. All NEW files with env vars will be placed there. If env files already exists, we supplement them with new env vars. Just pass the string with absolute path under this line:')
    root_dir = input()
    return root_dir


def define_env_files_types():
    print(
        'Which type of files do u need? 1 - .env, 2 - .envrc, 3 - pytest.ini. Pass string, that contains numbers of strings under this line. Write numbers together without any separator')
    files_types = []
    numbers = input()

    if '1' in numbers: files_types.append('.env')
    if '2' in numbers: files_types.append('.envrc')
    if '3' in numbers: files_types.append('pytest.ini')

    return files_types


def search_for_env_files(files_types, root_dir):
    path_to_env_files = {}

    for file_type in files_types:
        bashCommand = f'find {root_dir} -iname "*{file_type}"'
        # TODO: здесь может быть дохерища файлов с одинаковым расширением. Нужно будет спросить, какой нужен
        fp = subprocess.check_output(bashCommand, shell=True).decode('utf-8').replace('\n', '')
        if fp:
            path_to_env_files[file_type] = fp
        else:
            path_to_env_files[file_type] = ''

    return path_to_env_files


def find_existed_envs():
    # bash command: find /home/valera/PycharmProjects/notion_plugin -name "*.py" | xargs -d '\n' grep -ho "os.environ.*" | grep -o --regexp="'.*'" | grep -o --regexp='\\w.*\\w'
    # TODO: нужно сделать, чтоб несколько переменных в одну строку разделялись
    bashCommand = 'find /home/valera/PycharmProjects/notion_plugin -name "*.py" | xargs -d "\n" grep -ho "os.environ.*" | grep -o --regexp="\'.*\'" | grep -o --regexp="\\w.*\\w"'
    process = subprocess.check_output(bashCommand, shell=True).decode('utf-8').split('\n')

    # чищу пустые и дублирующиеся элементы
    envs = list(set([elem for elem in process if elem]))

    # for env in envs:
    # if ',' in env or ' ' in env or '"' in env or ']' in env :
    #     env.replace("'", '').replace("]", '').replace()

    # TODO: в результате нужно прихуярить ему возможность для взаимодействия из shell. Типа, шоб можно было командами управлять. Например, сделать замену переменной определенной
    # print('We found ')
    return envs


def define_envs_values():
    # TODO: вывести текущие значения переменных среды и проверить
    envs = {}
    existed_envs = find_existed_envs()
    for env in existed_envs:
        print(f'Type value of env var "{env}" under this sign. Type s for skip (if u dont want to set this env var)"')
        value = input()
        if value == 's':
            continue
        envs[env] = value

    return envs


# разбить файл построчно, положить значения в список
# проверить, содержит ли существущий .env файл переменную среды
# понять, на какой строке была переменная среды
# заменить эту строку

# TODO: type hinting прихуярить
def format_file(file_type: str, file_data: list, envs):

    if file_type == '.env':
        for env_name, env_value in envs.items():
            for count, line in enumerate(file_data):
                if env_name in line:
                    file_data[count] = f'{env_name}={env_value}'

    elif file_type == '.envrc':
        for env_name, env_value in envs.items():
            for count, line in enumerate(file_data):
                if env_name in line:
                    file_data[count] = f'export {env_name}={env_value}'

    # TODO: надо вспомнить, на каком моменте мы проверяем наличие файла. И создаем ли его заново. От этого зависит, будем ли мы прописывать env= в pytest.ini файле. Если просто редактируем, все ок. А если создаем заново, нужно иначе
    elif file_type == 'pytest.ini':
        for env_name, env_value in envs.items():
            for count, line in enumerate(file_data):
                if env_name in line:
                    file_data[count] = f'    {env_name}={env_value}'
    return file_data


def change_env_files(file_type: str, envs: dict, fp: str):

    with open(fp, 'r') as file:
        lines = file.read().splitlines()
        # TODO: сменить режим чтения на r либо разобраться в том, как mod "a+" включается. потом прочесть файл,
        formatted_structure = format_file(file_type, lines, envs)

    with open(fp, 'w') as file:
        file.write('\n'.join(formatted_structure))

def create_env_files(envs: dict, envs_fp: dict):

    file_type = [*envs_fp][0]
    if file_type == '.env':
        lines = [f'{env_name}={env_value}' for env_name, env_value in envs.items()]

    elif file_type == '.envrc':
        lines = [f'export {env_name}={env_value}' for env_name, env_value in envs.items()]

    elif file_type == 'pytest.ini':
        lines = [f'    {env_name}={env_value}' for env_name, env_value in envs.items()]
        lines.insert(0, '[pytest]')
        lines.insert(1, 'env=')

    with open(f'{ROOT_DIR}/{file_type}', 'w') as file:
        file.write('\n'.join(lines))

def dump_in_env_file(envs: dict, envs_fp: dict):
    # если файл существует, меняем строки местами:
    for file_type, fp in envs_fp.items():

        if file_type and Path(fp).is_file():
            change_env_files(file_type, envs, fp)
            print('Envs were changed in existing files')

        # если файл не существует, форматируем и дампим
        else:
            create_env_files(envs, envs_fp)
            print('Envs were dumped in files')


# def dump_envs_in_files(files_):

ROOT_DIR = define_root_dir()

# print(ROOT_DIR)
FILES_TYPES = define_env_files_types()
# print(FILES_TYPES)
ENVS_FP = search_for_env_files(FILES_TYPES, ROOT_DIR)
# print(ENVS_FP)
ENVS = define_envs_values()
# print(ENVS)

dump_in_env_file(ENVS, ENVS_FP)
