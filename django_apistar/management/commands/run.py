
from django.core.management.base import BaseCommand
from apistar.commands.run import run_wsgi

from django_apistar.wsgi import application


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        return run_wsgi(application)
