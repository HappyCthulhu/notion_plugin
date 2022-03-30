from app import celery
from backend.helpers.collect_pages_for_removing import collect_pages_for_removing
from backend.helpers.notion_tracking import notion_tracking


# celery -A backend.tasks worker --beat --loglevel=info -f path_to_celery_log_file

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # .s позволяет осуществить сторонний вызов функции test - через redis
    # 4.0 - через сколько вызывать функцию после конфигурации приложения
    # delay нужен когда внутри других функций вызываю либо delay либо здесь. delay - вызов сразу же
    # expires - через какое время убивать таску
    sender.add_periodic_task(1.0, collect_pages_for_removing.s(), expires=180)
    sender.add_periodic_task(20.0, notion_tracking.s(), expires=600)
