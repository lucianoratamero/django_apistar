
from unittest.mock import patch, call

from apistar.server.components import Component
from apistar.test import _TestClient
from django.test import TestCase
from django.test.utils import override_settings
from django.core.management.base import BaseCommand

import tests
from tests import test_settings
from django_apistar import test, wsgi


class FakeRequest:
    def __init__(self, path='/fake/'):
        self.environ = {'PATH_INFO': path}


class TestTestClient(TestCase):

    def test_test_client_inherits_from_correct_class(self):
        assert issubclass(test.TestClient, _TestClient)

    @patch('django_apistar.test._TestClient.__init__')
    @patch('django_apistar.test.application')
    def test_test_client_uses_application_at_init(self, mocked_app, mocked_init):
        mocked_init.return_value = None
        test.TestClient()
        mocked_init.assert_called_once_with(mocked_app, 'http', 'testserver')


class TestTestCase(TestCase):

    def test_test_case_inherits_from_django_test_case(self):
        assert issubclass(test.TestCase, TestCase)

    @patch('django_apistar.test.application')
    def test_test_case_initializes_with_correct_attrs(self, mocked_app):
        test_case = test.TestCase()
        self.assertEqual(test.TestClient, test_case.client_class)
        self.assertEqual(mocked_app.apistar_wsgi_app.reverse_url, test_case.reverse_url)


class TestWSGIApp(TestCase):

    def setUp(self):
        tests.routes = []

    @patch('django_apistar.wsgi.WSGIApp')
    @override_settings(APISTAR_SETTINGS={
        'COMPONENTS': ['fake_component'],
        'EVENT_HOOKS': ['fake_hooks'],
    })
    def test_passes_on_apistar_settings_to_app(self, mocked_app):
        wsgi.DjangoAPIStarWSGIApplication()
        mocked_app.assert_called_once_with(
            components=['fake_component'],
            event_hooks=['fake_hooks'],
            docs_url=None, routes=[]
        )

    @patch('django_apistar.wsgi.Include')
    def test_initializes_static_and_docs_if_debug_true(self, mocked_include):
        app = wsgi.DjangoAPIStarWSGIApplication()
        self.assertEqual(1, len(app.apistar_wsgi_app.router.name_lookups))
        assert 'serve_documentation' not in app.apistar_wsgi_app.router.name_lookups
        assert 'static' not in app.apistar_wsgi_app.router.name_lookups

        with override_settings(DEBUG=True):
            app = wsgi.DjangoAPIStarWSGIApplication()
            self.assertEqual(3, len(app.apistar_wsgi_app.router.name_lookups))
            assert 'serve_documentation' in app.apistar_wsgi_app.router.name_lookups
            assert 'static' in app.apistar_wsgi_app.router.name_lookups

    def test_is_allowed_django_route_method(self):
        app = wsgi.DjangoAPIStarWSGIApplication()
        self.assertIsNone(app.is_allowed_django_route('/fake/'))

        with override_settings(APISTAR_SETTINGS={'ALLOWED_DJANGO_ROUTES': ('/fake/',)}):
            self.assertEqual('/fake/', app.is_allowed_django_route('/fake/'))
            self.assertEqual('/fake/lala/', app.is_allowed_django_route('/fake/lala/'))

    @patch('django_apistar.wsgi.StaticFilesHandler')
    def test_calls_django_static_handler_if_path_startswith_static(self, mocked_handler):
        app = wsgi.DjangoAPIStarWSGIApplication()
        app({'PATH_INFO': '/static/lulu'}, None)
        mocked_handler.assert_called_once_with(app.django_wsgi_app)
        mocked_handler().assert_called_once_with({'PATH_INFO': '/static/lulu'}, None)

    @override_settings(STATIC_URL='/other_static/')
    @patch('django_apistar.wsgi.StaticFilesHandler')
    def test_calls_django_static_handler_if_path_startswith_different_static_url(self, mocked_handler):
        app = wsgi.DjangoAPIStarWSGIApplication()
        app({'PATH_INFO': '/other_static/lulu'}, None)
        mocked_handler.assert_called_once_with(app.django_wsgi_app)
        mocked_handler().assert_called_once_with({'PATH_INFO': '/other_static/lulu'}, None)

    @override_settings(APISTAR_SETTINGS={'ALLOWED_DJANGO_ROUTES': ('/fake/',)})
    @patch('django_apistar.wsgi.get_wsgi_application')
    def test_uses_django_app_if_route_is_allowed(self, mocked_get_app):
        app = wsgi.DjangoAPIStarWSGIApplication()
        mocked_get_app.assert_called_once_with()
        self.assertEqual(mocked_get_app(), app.django_wsgi_app)

        app({'PATH_INFO': '/fake/'}, None)
        mocked_get_app().assert_called_once_with({'PATH_INFO': '/fake/'}, None)

    @patch('django_apistar.wsgi.WSGIApp')
    def test_uses_apistar_app_as_default(self, mocked_app):
        app = wsgi.DjangoAPIStarWSGIApplication()
        mocked_app.assert_called_once_with(
            components=[], docs_url=None, event_hooks=[], routes=[]
        )
        self.assertEqual(mocked_app(), app.apistar_wsgi_app)

        app({'PATH_INFO': '/fake/'}, None)
        mocked_app().assert_called_once_with({'PATH_INFO': '/fake/'}, None)
