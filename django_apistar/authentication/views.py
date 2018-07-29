
from apistar import http
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist

from . import schemas


def token_login(user: schemas.TokenUser):
    from django_apistar.authentication.models import Token

    if not user:
        return http.JSONResponse({"message": "Invalid credentials."}, status_code=400)

    user = authenticate(username=user['username'], password=user['password'])

    if user:
        try:
            return user.auth_token.key
        except ObjectDoesNotExist:
            token = Token(user=user)
            token.save()
            return user.auth_token.key

    else:
        return http.JSONResponse({"message": "Invalid credentials."}, status_code=400)


def token_logout(authorization: http.Header):
    from django_apistar.authentication.models import Token
    if not authorization:
        return None

    scheme, token = authorization.split()
    if scheme.lower() != 'bearer':
        return None

    try:
        user = Token.objects.get(key=token).user
    except Token.DoesNotExist:
        return None

    if user:
        user.auth_token.delete()

    return http.JSONResponse({"message": "Logged out."}, status_code=200)
