
import os
from importlib import import_module

from apistar import Include
from apistar.frameworks.wsgi import WSGIApp
from apistar.handlers import docs_urls, static_urls

import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_apistar_example.settings")
django.setup()


class DjangoAPIStarWSGIApplication:
    def __init__(self):
        routes = import_module(settings.APISTAR_ROUTE_CONF).routes

        if settings.DEBUG:
            routes.append(Include('/static', static_urls))
            routes.append(Include('/docs', docs_urls))

        self.django_wsgi_app = get_wsgi_application()
        self.apistar_wsgi_app = WSGIApp(routes=routes, settings=settings.APISTAR_SETTINGS)

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
