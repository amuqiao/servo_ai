import logging
from src.celery_app import app
from celery import shared_task
from kafka import KafkaProducer


@app.task
def test_task():
    return "Celery worker is functioning properly"


# 与CeleryConfig中CELERY_BEAT_SCHEDULE的task路径一致

