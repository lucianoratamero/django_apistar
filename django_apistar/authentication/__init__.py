
from apistar import Route

from . import views


routes = [
    Route('/token-login/', 'POST', views.token_login),
    Route('/token-logout/', 'GET', views.token_logout),
]