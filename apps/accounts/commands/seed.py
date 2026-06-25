from django.core.management.base import BaseCommand
from apps.accounts.models import Agent

class Command(BaseCommand):
    help = 'Seeds the database with initial agent account'

    def handle(self, *args, **kwargs):
        if not Agent.objects.filter(email='admin@test.com').exists():
            Agent.objects.create_superuser(
                email='admin@test.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Agent created: admin@test.com'))
        else:
            self.stdout.write('Agent already exists, skipping.')
