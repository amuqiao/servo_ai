from celery import Celery
import os

app = Celery(__name__)
app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://:difyai123456@redis:6379/0')
app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://:difyai123456@redis:6379/0')
app.autodiscover_tasks(packages=['src.celery_app'], related_name='tasks')
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']