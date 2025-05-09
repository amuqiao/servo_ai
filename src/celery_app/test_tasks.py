from .celery_app import app
from kafka import KafkaProducer

@app.task
def test_task():
    return "Celery worker is functioning properly"

