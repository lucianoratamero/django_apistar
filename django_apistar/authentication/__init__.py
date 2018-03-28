
import base64
import typing
from apistar import http
from apistar import Route
from apistar.interfaces import Auth
from django.contrib.auth import authenticate

from . import views


routes = [
    Route('/token-login/', 'POST', views.token_login),
    Route('/token-logout/', 'GET', views.token_logout),
]


class DjangoAuth(Auth):
    def __init__(self, user=None, token=None):
        super().__init__()
        self.user = user
        self.token = token

    def is_authenticated(self) -> bool:
        if self.user:
            return self.user.is_authenticated

    def get_display_name(self) -> typing.Optional[str]:
        if self.user:
            return self.user.username

    def get_user_id(self) -> typing.Optional[str]:
        if self.user:
            return self.user.id


class DjangoBasicAuthentication():
    def authenticate(self, authorization: http.Header):
        """
        Determine the user associated with a request, using HTTP Basic Authentication.
        """
        if authorization is None:
            return None

        scheme, token = authorization.split()
        if scheme.lower() != 'basic':
            return None

        username, password = base64.b64decode(token).decode('utf-8').split(':')
        user = authenticate(username=username, password=password)

        if user:
            return DjangoAuth(user=user)


class DjangoTokenAuthentication():
    def authenticate(self, authorization: http.Header):
        """
        Determine the user associated with a request, using Token Authentication.
        """
        from django_apistar.authentication.models import Token

        if authorization is None:
            return None

        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            return None

        try:
            user = Token.objects.get(key=token).user
        except Token.DoesNotExist:
            return None

        if user:
            return DjangoAuth(user=user, token=user.auth_token.key)
