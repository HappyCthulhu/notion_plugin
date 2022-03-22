from app import celery
from backend.helpers.notion_tracking import notion_tracking
from backend.helpers.collect_pages_for_removing import collect_pages_for_removing
# celery -A backend.tasks worker --beat --loglevel=info

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # .s позволяет осуществить сторонний вызов функции test - через redis
    # 4.0 - через сколько вызывать функцию после конфигурации приложения
    # delay нужен когда внутри других функций вызываю либо delay либо здесь. delay - вызов сразу же
    # expires - через какое время убивать таску
    sender.add_periodic_task(4.0, collect_pages_for_removing.s(), expires=180)
    sender.add_periodic_task(10.0, notion_tracking.s(), expires=600)