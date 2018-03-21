
from django.http.response import HttpResponseNotFound

from django_apistar.apps import App


class RequestMiddleware:

    def __init__(self, get_response=None):
        self.get_response = get_response
        self.response_headers = []
        self.status_text = ''

    def __call__(self, request):
        response = None
        if hasattr(self, 'process_request'):
            response = self.process_request(request)
        if not response:
            response = self.get_response(request)
        if hasattr(self, 'process_response'):
            response = self.process_response(request, response)
        return response

    def process_apistar_response(self, status_text, headers):
        self.status_text = status_text
        self.response_headers = headers

    def process_response(self, request, response):
        path = request.environ['PATH_INFO']

        if path != '/' and not isinstance(response, HttpResponseNotFound):
            return response

        if not path.endswith('/') and not path.endswith('.js'):
            request.environ['PATH_INFO'] = path + '/'

        content = App(request.environ, self.process_apistar_response)

        if content:
            response.content = content

            try:
                response._headers['content-type'] = self.response_headers[0]
            except IndexError:
                pass

            try:
                status_code = int(self.status_text.split(' ')[0])
            except ValueError:
                status_code = 200

            response.status_code = status_code

        return response
