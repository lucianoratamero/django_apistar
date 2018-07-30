
from apistar import types, validators


class TokenUser(types.Type):
    username = validators.String()
    password = validators.String()
