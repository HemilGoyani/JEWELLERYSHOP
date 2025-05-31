import os
from celery import Celery
from celery.schedules import crontab 

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# create the Celery app instance
app = Celery('backend')

# load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# discover tasks across all apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Define a periodic task to print something every minute
app.conf.beat_schedule = {
    'print-every-minute': {
        'task': 'users.tasks.simple_print_task',  # This refers to the task defined in tasks.py
        'schedule': crontab(minute='*'),  # Run the task every minute
    },
}