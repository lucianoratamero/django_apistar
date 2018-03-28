
from apistar import typesystem


class TokenUser(typesystem.Object):
    required = ['username', 'password']
    properties = {
        'username': typesystem.String,
        'password': typesystem.String,
    }
