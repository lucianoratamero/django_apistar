import base64
import typing
from apistar import http
from apistar.server.components import Component
from django.contrib.auth import authenticate


class DjangoBasicAuthentication(Component):
    def resolve(self, authorization: http.Header):
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

        return user


class DjangoTokenAuthentication(Component):
    def resolve(self, authorization: http.Header):
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

        return user