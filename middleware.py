
from django.http.response import HttpResponseNotFound
from django.utils.deprecation import MiddlewareMixin

from django_apistar.apps import DjangoAPIStarConfig


class RequestMiddleware(MiddlewareMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = DjangoAPIStarConfig.run_app()
        self.response_headers = []
        self.status_text = ''

    def process_apistar_response(self, status_text, headers):
        self.status_text = status_text
        self.status_code = int(self.status_text.split(' ')[0])
        self.response_headers = headers

    def process_response(self, request, response):
        path = request.environ['PATH_INFO']

        if path != '/' and not isinstance(response, HttpResponseNotFound):
            return response

        content = self.app(request.environ, self.process_apistar_response)

        if not self.status_code == 404:
            response.content = content
            response._headers['content-type'] = self.response_headers[0]
            response.status_code = self.status_code

        return response
