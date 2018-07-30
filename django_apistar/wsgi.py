
import os
from importlib import import_module

from apistar.server.app import App as WSGIApp
from apistar.server.core import Include

import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_apistar_example.settings")
django.setup()


class DebugApp(WSGIApp):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug = True


class DjangoAPIStarWSGIApplication:
    def __init__(self):
        self.django_wsgi_app = get_wsgi_application()
        self.apistar_wsgi_app = self.get_apistar_wsgi_application()

    def get_apistar_wsgi_application(self):
        routes = import_module(settings.APISTAR_ROUTE_CONF).routes
        docs_url = '/docs/'

        if not settings.DEBUG:
            docs_url = None

        apistar_wsgi_app_class = WSGIApp

        if settings.DEBUG:
            apistar_wsgi_app_class = DebugApp

        return apistar_wsgi_app_class(
            routes=routes,
            docs_url=docs_url,
            components=settings.APISTAR_SETTINGS.get('COMPONENTS', []),
            event_hooks=settings.APISTAR_SETTINGS.get('EVENT_HOOKS', []),
        )

    def is_allowed_django_route(self, path):
        allowed_django_routes = settings.APISTAR_SETTINGS.get('ALLOWED_DJANGO_ROUTES', [])
        path_is_contained = [route for route in allowed_django_routes if path.startswith(route)]

        if path in allowed_django_routes or path_is_contained:
            return path

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']

        if settings.STATIC_URL is not None:
            static_url = settings.STATIC_URL
        else:
            static_url = '/static/'

        if path.startswith(static_url):
            return StaticFilesHandler(self.django_wsgi_app)(environ, start_response)

        if self.is_allowed_django_route(path):
            return self.django_wsgi_app(environ, start_response)

        return self.apistar_wsgi_app(environ, start_response)


application = DjangoAPIStarWSGIApplication()
