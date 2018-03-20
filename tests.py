
from unittest.mock import patch, call

from apistar import http
from apistar.interfaces import Auth
from apistar.frameworks.wsgi import WSGIApp
from apistar.handlers import docs_urls, static_urls
from django.test import TestCase
from django.test.utils import override_settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User
from django.http.response import HttpResponse, HttpResponseNotFound

from django_apistar import apps, auth, middleware


routes = []  # used to simulate a route conf module


class FakeRequest:
    def __init__(self, path='/fake/'):
        self.environ = {'PATH_INFO': path}


class TestDjangoAPIStarApps(TestCase):

    def test_app_has_correct_name(self):
        self.assertEqual('django_apistar', apps.DjangoAPIStarConfig.name)

    @override_settings(APISTAR_ROUTE_CONF='')
    def test_run_app_without_route_conf(self):
        self.assertRaises(ImproperlyConfigured, apps.DjangoAPIStarConfig.run_app)

    @patch('django_apistar.apps.Include')
    @override_settings(APISTAR_ROUTE_CONF='django_apistar.tests')
    def test_app_adds_static_and_docs_urls_if_debug(self, mocked_include):
        app = apps.DjangoAPIStarConfig.run_app()
        self.assertEqual(0, len(app.router._routes))
        self.assertEqual(0, mocked_include.call_count)

        with override_settings(DEBUG=True):
            app = apps.DjangoAPIStarConfig.run_app()
            self.assertEqual(2, len(app.router._routes))
            self.assertEqual(2, mocked_include.call_count)
            self.assertIn(call('/static/', static_urls), mocked_include.call_args_list)
            self.assertIn(call('/docs/', docs_urls), mocked_include.call_args_list)

    def test_app_is_wsgiapp_subclass(self):
        assert issubclass(apps.DjangoAPIStarApp, WSGIApp)

    def test_app_has_run_command_bound_to_none(self):
        commands = apps.DjangoAPIStarApp.BUILTIN_COMMANDS
        self.assertEqual(1, len(commands))
        self.assertEqual('run', commands[0].name)
        self.assertEqual(None, commands[0].handler())


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


class TestRequestMiddleware(TestCase):

    def setUp(self):
        self.patcher = patch('django_apistar.middleware.App')
        self.mocked_app = self.patcher.start()
        self.middleware = middleware.RequestMiddleware

    def tearDown(self):
        self.patcher.stop()

    def test_initializes_with_headers_and_status_text(self):
        instance = self.middleware()

        self.assertEqual([], instance.response_headers)
        self.assertEqual('', instance.status_text)

    def test_ignores_apistar_if_not_root_path_and_not_404(self):
        request = FakeRequest()
        response = HttpResponse()

        instance = self.middleware()

        self.assertEqual(response, instance.process_response(request, response))

    def test_ignores_apistar_if_it_returns_404(self):
        self.mocked_app().return_value = [b'']
        request = FakeRequest()
        response = HttpResponseNotFound()

        instance = self.middleware()
        instance.status_code = 404

        self.assertEqual(response, instance.process_response(request, response))

    def test_returns_apistar_response_otherwise(self):
        request = FakeRequest()
        response = HttpResponseNotFound()

        instance = self.middleware()
        instance.response_headers = [['headers']]
        instance.status_code = 200

        apistar_response = instance.process_response(request, response)

        self.mocked_app.assert_called_with(request.environ, instance.process_apistar_response)
        self.assertEqual(200, apistar_response.status_code)
        self.assertEqual(instance.response_headers[0], apistar_response._headers['content-type'])
