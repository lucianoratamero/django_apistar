
from apistar.test import _TestClient
from django.test import TestCase as DjangoTestCase

from django_apistar.wsgi import application


class TestClient(_TestClient):
    def __init__(self, *args, **kwargs):
        return super().__init__(application, 'http', 'testserver')


class TestCase(DjangoTestCase):
    client_class = TestClient

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reverse_url = application.apistar_wsgi_app.reverse_url
