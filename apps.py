from importlib import import_module

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from apistar import Include
from apistar.core import Command
from apistar.handlers import docs_urls, static_urls
from apistar.frameworks.wsgi import WSGIApp


class DjangoAPIStarConfig(AppConfig):
    """Lean AppConfig for binding API Star to Django"""

    name = 'django_apistar'
    verbose_name = "Django API Star"

    @staticmethod
    def run_app():
        try:
            routes = import_module(settings.APISTAR_ROUTE_CONF).routes
        except ValueError:
            raise ImproperlyConfigured('APISTAR_ROUTE_CONF needs to be declared in your Django settings.')

        if settings.DEBUG:
            '''
            We need to include the static urls, even though we won't use them,
            to prevent an API Star exception.
            '''
            routes.append(Include('/static/', static_urls))
            routes.append(Include('/docs/', docs_urls))

        return DjangoAPIStarApp(
            routes=routes,
            settings=settings.APISTAR_SETTINGS,
            components=settings.APISTAR_SETTINGS.get('COMPONENTS', [])
        )


class DjangoAPIStarApp(WSGIApp):
    """Main Django API Star app. Overwrites WSGI command to hijack Django's WSGI app."""
    BUILTIN_COMMANDS = [Command('run', lambda: None)]


App = DjangoAPIStarConfig.run_app()
