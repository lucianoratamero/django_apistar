import os

DIRNAME = os.path.dirname(__file__)

SECRET_KEY = 'o=v^sgst0up0^znuce#97(6o5uwxi+nv!ur@b(6(js50808(%&'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'database.db',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'tests',
)

APISTAR_SETTINGS = {'DATABASES': DATABASES}
APISTAR_ROUTE_CONF = 'tests'

MIDDLEWARE = ['django_apistar.middleware.RequestMiddleware']  # for django 2+
MIDDLEWARE_CLASSES = ['django_apistar.middleware.RequestMiddleware']
