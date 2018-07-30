
from unittest.mock import patch

from apistar import http
from django.test import TestCase
from django.contrib.auth.models import User

from django_apistar.authentication import components, models, views


class TestDjangoBasicAuthentication(TestCase):

    def setUp(self):
        self.authenticator = components.DjangoBasicAuthentication()

    def test_returns_none_if_no_headers_are_passed(self):
        self.assertIsNone(self.authenticator.resolve(None))

    def test_returns_none_if_scheme_is_not_basic(self):
        auth_header = http.Header('not_basic token')
        self.assertIsNone(self.authenticator.resolve(auth_header))

    def test_returns_none_if_django_does_not_resolve_user(self):
        auth_header = http.Header('Basic dXNlcm5hbWU6cGFzc3dvcmQ=')
        self.assertIsNone(self.authenticator.resolve(auth_header))

    def test_returns_user_if_resolve_user(self):
        user = User(username='username')
        user.set_password('password')
        user.save()

        auth_header = http.Header('Basic dXNlcm5hbWU6cGFzc3dvcmQ=')
        auth_user = self.authenticator.resolve(auth_header)

        self.assertEqual(user, auth_user)



class TestDjangoTokenAuthentication(TestCase):

    def setUp(self):
        self.authenticator = components.DjangoTokenAuthentication()

    def test_returns_none_if_no_headers_are_passed(self):
        self.assertIsNone(self.authenticator.resolve(None))

    def test_returns_none_if_scheme_is_not_bearer(self):
        auth_header = http.Header('not_bearer token')
        self.assertIsNone(self.authenticator.resolve(auth_header))

    def test_returns_none_if_django_does_not_resolve_user(self):
        auth_header = http.Header('Bearer dXNlcm5hbWU6cGFzc3dvcmQ=')

        self.assertIsNone(self.authenticator.resolve(auth_header))

    def test_returns_user_if_resolve_user(self):
        user = User(username='username')
        user.set_password('password')
        user.save()

        token = models.Token(user=user)
        token.save()

        auth_header = http.Header(f'Bearer {token.key}')
        auth_user = self.authenticator.resolve(auth_header)

        self.assertEqual(user, auth_user)


class TestTokenAuthViews(TestCase):

    def setUp(self):
        self.user = User(username='username')
        self.user.set_password('dXNlcm5hbWU6cGFzc3dvcmQ=')
        self.user.save()

    def test_token_login_view_400_for_wrong_credentials(self):
        response = views.token_login(user={})
        self.assertEqual(400, response.status_code)

        response = views.token_login(user={
            'username': 'lala',
            'password': 'lala'
        })
        self.assertEqual(400, response.status_code)

    def test_token_login_view_returns_correct_token(self):
        self.user.auth_token = models.Token()
        self.user.auth_token.save()

        response = views.token_login(user={
            'username': self.user.username,
            'password': 'dXNlcm5hbWU6cGFzc3dvcmQ=',
        })

        self.assertEqual(self.user.auth_token.key, response)

    def test_token_logout_returns_204_for_no_authorization(self):
        response = views.token_logout(authorization=None)
        self.assertIsNone(response)

    def test_token_logout_returns_204_for_no_bearer_auth(self):
        response = views.token_logout(authorization=http.Header('not_bearer token'))
        self.assertIsNone(response)

    def test_token_logout_returns_204_for_no_token_related(self):
        response = views.token_logout(authorization=http.Header('Bearer invalid_token'))
        self.assertIsNone(response)

    def test_token_logout_returns_200_when_deleting_token(self):
        self.user.auth_token = models.Token()
        self.user.auth_token.save()
        self.assertEqual(1, models.Token.objects.count())

        response = views.token_logout(authorization=http.Header('Bearer {}'.format(self.user.auth_token.key)))

        self.assertEqual(0, models.Token.objects.count())
        self.assertEqual(200, response.status_code)
        self.assertEqual(b'{"message":"Logged out."}', response.content)
