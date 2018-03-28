
from unittest.mock import patch

from apistar import http
from apistar.interfaces import Auth
from django.test import TestCase
from django.contrib.auth.models import User

from django_apistar import authentication


class TestDjangoAuth(TestCase):

    def test_django_auth_is_apistar_auth_subclass(self):
        assert issubclass(authentication.DjangoAuth, Auth)

    def test_django_auth_integrates_with_default_user_model(self):
        user = User(username='test', id=123)
        auth_user = authentication.DjangoAuth(user=user)

        self.assertEqual(user.is_authenticated, auth_user.is_authenticated())
        self.assertEqual(user.id, auth_user.get_user_id())
        self.assertEqual(user.username, auth_user.get_display_name())
        self.assertEqual(user, auth_user.user)


class TestDjangoBasicAuthentication(TestCase):

    def setUp(self):
        self.authenticator = authentication.DjangoBasicAuthentication()

    def test_returns_none_if_no_headers_are_passed(self):
        self.assertIsNone(self.authenticator.authenticate(None))

    def test_returns_none_if_scheme_is_not_basic(self):
        auth_header = http.Header('not_basic token')
        self.assertIsNone(self.authenticator.authenticate(auth_header))

    @patch('django_apistar.authentication.authenticate')
    def test_returns_none_if_django_does_not_authenticate_user(self, mocked_authenticate):
        mocked_authenticate.return_value = None
        auth_header = http.Header('Basic dXNlcm5hbWU6cGFzc3dvcmQ=')

        self.assertIsNone(self.authenticator.authenticate(auth_header))
        mocked_authenticate.assert_called_once_with(username='username', password='password')

    @patch('django_apistar.authentication.authenticate')
    def test_returns_django_auth_instance_if_django_authenticates_user(self, mocked_authenticate):
        mocked_authenticate.return_value = User()
        auth_header = http.Header('Basic dXNlcm5hbWU6cGFzc3dvcmQ=')

        auth_user = self.authenticator.authenticate(auth_header)

        assert isinstance(auth_user, authentication.DjangoAuth)
        mocked_authenticate.assert_called_once_with(username='username', password='password')


class TestDjangoTokenAuthentication(TestCase):

    def setUp(self):
        self.authenticator = authentication.DjangoTokenAuthentication()

    def test_returns_none_if_no_headers_are_passed(self):
        self.assertIsNone(self.authenticator.authenticate(None))

    def test_returns_none_if_scheme_is_not_bearer(self):
        auth_header = http.Header('not_bearer token')
        self.assertIsNone(self.authenticator.authenticate(auth_header))

    def test_returns_none_if_django_does_not_authenticate_user(self):
        auth_header = http.Header('Bearer dXNlcm5hbWU6cGFzc3dvcmQ=')

        self.assertIsNone(self.authenticator.authenticate(auth_header))

    def test_returns_django_auth_instance_if_django_authenticates_user(self):
        user = User(username='test')
        user.save()
        user.auth_token = authentication.models.Token()
        user.auth_token.save()

        auth_header = http.Header('Bearer {}'.format(user.auth_token.key))
        auth_user = self.authenticator.authenticate(auth_header)

        assert isinstance(auth_user, authentication.DjangoAuth)
        assert user == auth_user.user
        assert user.auth_token.key == auth_user.token


class TestTokenAuthViews(TestCase):

    def setUp(self):
        self.user = User(username='username')
        self.user.set_password('dXNlcm5hbWU6cGFzc3dvcmQ=')
        self.user.save()

    def test_token_login_view_400_for_wrong_credentials(self):
        response = authentication.views.token_login(user={})
        self.assertEqual(400, response.status)

        response = authentication.views.token_login(user={
            'username': 'lala',
            'password': 'lala'
        })
        self.assertEqual(400, response.status)

    def test_token_login_view_returns_correct_token(self):
        self.user.auth_token = authentication.models.Token()
        self.user.auth_token.save()

        response = authentication.views.token_login(user={
            'username': self.user.username,
            'password': 'dXNlcm5hbWU6cGFzc3dvcmQ=',
        })

        self.assertEqual(self.user.auth_token.key, response)

    def test_token_logout_returns_204_for_no_authorization(self):
        response = authentication.views.token_logout(authorization=None)
        self.assertIsNone(response)

    def test_token_logout_returns_204_for_no_bearer_auth(self):
        response = authentication.views.token_logout(authorization=http.Header('not_bearer token'))
        self.assertIsNone(response)

    def test_token_logout_returns_204_for_no_token_related(self):
        response = authentication.views.token_logout(authorization=http.Header('Bearer invalid_token'))
        self.assertIsNone(response)

    def test_token_logout_returns_200_when_deleting_token(self):
        self.user.auth_token = authentication.models.Token()
        self.user.auth_token.save()
        self.assertEqual(1, authentication.models.Token.objects.count())

        response = authentication.views.token_logout(authorization=http.Header('Bearer {}'.format(self.user.auth_token.key)))

        self.assertEqual(0, authentication.models.Token.objects.count())
        self.assertEqual(200, response.status)
        self.assertEqual({"message": "Logged out."}, response.content)
