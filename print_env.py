import os

try:
    if os.environ['ROOT_PATH_DIR']:
        print('I can access to env vars!')
    else:
        print('Env var in empty... But, at least i have access to env vars!')
except:
    print('Cant get access to env vars((')
