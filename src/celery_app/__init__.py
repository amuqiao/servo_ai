from celery import Celery
import os

app = Celery(__name__)

app.autodiscover_tasks(packages=['src.celery_app'], related_name='tasks')



