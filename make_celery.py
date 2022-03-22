from celery import Celery
from config import Config

# TODO: они везде предлагают создать функ-ю make_celery и вынести ее в файл celery_utils, но это потребует импортировать туда app. А следовательно, может повлечь циклический импорт, если из app.py будем запускать make_celery
# TODO: правильно понимаю, что эта штука нужна для того, чтоб передать контекст приложения?
# передача параметра в функцию не приведет к циклическому импорту
def make_celery(app):
    ### Instantiate Celery ###
    celery = Celery(
        app.import_name,
        backend=Config.CELERY_RESULT_BACKEND,
        broker=Config.CELERY_BROKER_URL
    )

    # Configure celery
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    celery.config_from_object(__name__)
    return celery
