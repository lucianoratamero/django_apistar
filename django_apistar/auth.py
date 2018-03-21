
import base64
import typing
from apistar import http
from apistar.interfaces import Auth
from django.contrib.auth import authenticate


class DjangoAuth(Auth):
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        return super().__init__(*args, **kwargs)

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
