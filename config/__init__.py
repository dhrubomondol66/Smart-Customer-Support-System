# This makes Celery load when Django starts
# so shared_task decorator works in tasks.py
from .celery import app as celery_app

__all__ = ('celery_app',)