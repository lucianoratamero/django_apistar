
from apistar import http, exceptions
from apistar.server.wsgi import WSGIStartResponse, WSGIEnviron
from django.conf import settings


class MustBeAuthenticated():
    def on_request(self, authorization: http.Header, request: http.Request):
        if '/auth/' in request.url:
            return

        is_authenticated = False

        for auth_component in settings.APISTAR_SETTINGS.get('AUTH_COMPONENTS', []):
            user = auth_component.resolve(authorization)
            if user:
                is_authenticated = True

        if not is_authenticated:
            raise exceptions.HTTPException({'message': 'User must be logged in.'}, status_code=403)