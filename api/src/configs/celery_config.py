from celery.schedules import crontab

beat_schedule = {
    'heartbeat-task': {
        'task': 'tasks.heartbeat',
        'schedule': crontab(minute='*/5'),
        'args': ()
    }
}