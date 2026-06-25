import os
from celery import Celery
from django.conf import settings

# Tell Celery which Django settings to use
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('support_inbox')

# Pull Celery config from Django settings
# namespace='CELERY' means all celery settings in settings.py
# must start with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in all INSTALLED_APPS
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Built-in health check task.
    Run: docker-compose exec web celery -A config inspect ping
    """
    print(f'Celery is working! Request: {self.request!r}')