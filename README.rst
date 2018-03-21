django_apistar
==============

.. image:: https://travis-ci.org/lucianoratamero/django_apistar.svg?branch=master
    :target: https://travis-ci.org/lucianoratamero/django_apistar

This project is a `Django`_ App that hooks up Django with the `API
Star`_\ ’s routes and views. The aim is to have API Star as the API
frontend, while having the whole Django toolset available for devs to
work with.

Both API Star’s docs and Django Admin work as intended.

Suppports:

- django>=1.8
- apistar>=0.3.5

Installation
~~~~~~~~~~~~

For now, we don’t have this project registered at PyPI, so the only way
to install it is to clone it and use it as another Django App: putting
it into your project.

After putting the code into your Django project, we need to set up a
couple of things. First, we need to add ``django_apistar`` to your
``INSTALLED_APPS`` in your project’s ``settings.py``:

.. code:: python

    INSTALLED_APPS = (
        ...
        'django_apistar',
        'your_api_star_app',
        ...
    )

Then, we need to register our request middleware. **Since we need to
modify responses, the lower you can put the middleware, the better.**

.. code:: python

    MIDDLEWARE = [
        ...,
        'django_apistar.middleware.RequestMiddleware',
    ]

Finally, we need two settings set if we want to use ``apistar``: a base
route module (``APISTAR_ROUTE_CONF``) and API Star’s own settings. After
you’ve defined the databases in your settings file:

.. code:: python

    DATABASES = {
        ...
    }

    APISTAR_SETTINGS = {
        'DATABASES': DATABASES,
    }

    APISTAR_ROUTE_CONF = 'your_api_star_app.routes'

You may as well disable unused middlewares to speed up the response
time.

Authentication
~~~~~~~~~~~~~~

For now, we only provide a class for Basic authentication.

To use it, configure your ``APISTAR_SETTINGS`` as you would configure
your API Star app:

.. code:: python

    from django_apistar.auth import DjangoBasicAuthentication

    ...

    APISTAR_SETTINGS['AUTHENTICATION'] = [DjangoBasicAuthentication()],

How it works
~~~~~~~~~~~~

The way this app works is by faking an API Star WSGIApp while hijacking
Django’s own process and using the API Star app whenever Django can’t
respond to a request (404).

When responding a request, if Django responded 404, our middleware kicks
in and tries to respond it using the API Star routes and views. **Keep
in mind that even using this app, Django’s routes take precedence**.

Implementing views
''''''''''''''''''

There is no need to think about corner cases when writing views. We only
need to keep in mind that we won’t be able to use the ``django_orm``
backend baked into API Star, so we must access models directly to deal
with CRUD operations.

For example, let’s create a view that persists a ``Product``:

.. code:: python

    from core import schemas
    from core.models import Product

    def create_product(product: schemas.Product):
        db_product = Product(**product)
        db_product.save()
        return http.Response(content=schemas.Product(db_product.__dict__), status=201)

As intended, all the data validation is at the schemas, and everything
is handled my API Star.

Implementing tests
''''''''''''''''''

To test your API Star views, we can make use of the whole Django test
framework. The only main difference is that we can’t use Django’s test
client, since it’s tuned to work with Django views. We can, though, use
API Star’s own test client:

.. code:: python

    from django.test import TestCase
    from apistar.test import TestClient
    from model_mommy import mommy
    from django_apistar.apps import App

    from core import models, schemas


    class TestListProducts(TestCase):

        def test_list_products(self):
            client = TestClient(App)
            url = App.reverse_url('list_products')
            produto = mommy.make(models.Product, rating=5, size='large')

            response = client.get(url)
            content = response.json()

            expected_product = schemas.Product(product.__dict__)
            self.assertEqual(1, len(content))
            self.assertEqual(expected_product, content[0])

Contributing
~~~~~~~~~~~~

There are still a lot of ways we can improve and add more features to
this app. If you find any bugs or have significant suggestions, just
open an issue or contact me at luciano@ratamero.com. Pull requests will
be received with all care and attention as well :)

.. _Django: https://www.djangoproject.com/
.. _API Star: https://github.com/encode/apistar
