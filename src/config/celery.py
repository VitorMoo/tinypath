from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

from celery.schedules import crontab

app.conf.beat_schedule = {
    'periodic-scraping': {
        'task': 'scraping.tasks.periodic_scraping',
        'schedule': 3600.0,
    },
    'send-assignment-alerts': {
        'task': 'notifications.send_assignment_alerts',
        'schedule': crontab(hour=8, minute=0),  # Executa diariamente às 8:00 AM
    },
}
app.conf.timezone = 'UTC'
