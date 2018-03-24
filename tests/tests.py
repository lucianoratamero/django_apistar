
from unittest.mock import patch, call

from apistar import http
from apistar.test import _TestClient
from apistar.interfaces import Auth
from apistar.handlers import docs_urls, static_urls
from django.test import TestCase
from django.test.utils import override_settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

import tests
from tests import test_settings
from django_apistar import auth, test, wsgi
from django_apistar.management.commands.run import Command


class FakeRequest:
    def __init__(self, path='/fake/'):
        self.environ = {'PATH_INFO': path}


class TestDjangoAuth(TestCase):

    def test_django_auth_is_apistar_auth_subclass(self):
        assert issubclass(auth.DjangoAuth, Auth)

    def test_django_auth_integrates_with_default_user_model(self):
        user = User(username='test', id=123)
        auth_user = auth.DjangoAuth(user=user)

        self.assertEqual(user.is_authenticated, auth_user.is_authenticated())
        self.assertEqual(user.id, auth_user.get_user_id())
        self.assertEqual(user.username, auth_user.get_display_name())
        self.assertEqual(user, auth_user.user)


class TestDjangoBasicAuthentication(TestCase):

    def setUp(self):
        self.authenticator = auth.DjangoBasicAuthentication()

    def test_returns_none_if_no_headers_are_passed(self):
        self.assertIsNone(self.authenticator.authenticate(None))

    def test_returns_none_if_scheme_is_not_basic(self):
        auth_header = http.Header('not_basic token')
        self.assertIsNone(self.authenticator.authenticate(auth_header))

    @patch('django_apistar.auth.authenticate')
    def test_returns_none_if_django_does_not_authenticate_user(self, mocked_authenticate):
        mocked_authenticate.return_value = None
        auth_header = http.Header('Basic dXNlcm5hbWU6cGFzc3dvcmQ=')

        self.assertIsNone(self.authenticator.authenticate(auth_header))
        mocked_authenticate.assert_called_once_with(username='username', password='password')

    @patch('django_apistar.auth.authenticate')
    def test_returns_django_auth_instance_if_django_authenticates_user(self, mocked_authenticate):
        mocked_authenticate.return_value = User()
        auth_header = http.Header('Basic dXNlcm5hbWU6cGFzc3dvcmQ=')

        auth_user = self.authenticator.authenticate(auth_header)

        assert isinstance(auth_user, auth.DjangoAuth)
        mocked_authenticate.assert_called_once_with(username='username', password='password')


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


class TestRunCommand(TestCase):

    @patch('django_apistar.management.commands.run.application')
    @patch('django_apistar.management.commands.run.run_wsgi')
    def test_command_runs_correct_application(self, mocked_run_wsgi, mocked_app):
        assert issubclass(Command, BaseCommand)
        command = Command()
        command.handle()
        mocked_run_wsgi.assert_called_once_with(mocked_app)


class TestWSGIApp(TestCase):

    def setUp(self):
        tests.routes = []

    @patch('django_apistar.wsgi.Include')
    def test_initializes_static_and_docs_if_debug_true(self, mocked_include):
        app = wsgi.DjangoAPIStarWSGIApplication()
        self.assertEqual(0, len(app.apistar_wsgi_app.router._routes))
        self.assertEqual(0, mocked_include.call_count)

        with override_settings(DEBUG=True):
            app = wsgi.DjangoAPIStarWSGIApplication()
            self.assertEqual(2, len(app.apistar_wsgi_app.router._routes))
            self.assertEqual(2, mocked_include.call_count)
            self.assertIn(call('/static', static_urls), mocked_include.call_args_list)
            self.assertIn(call('/docs', docs_urls), mocked_include.call_args_list)
            app.apistar_wsgi_app.router._routes = []

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
        mocked_app.assert_called_once_with(routes=[], settings=test_settings.APISTAR_SETTINGS)
        self.assertEqual(mocked_app(), app.apistar_wsgi_app)

        app({'PATH_INFO': '/fake/'}, None)
        mocked_app().assert_called_once_with({'PATH_INFO': '/fake/'}, None)
