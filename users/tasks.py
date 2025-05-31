# backend/tasks.py
from celery import shared_task

@shared_task
def simple_print_task():
    print("This task runs every minute.")
