django_apistar
==============

**Note: since API Star is changing directions (https://github.com/encode/apistar/pull/624), this project is mostly on hold.
As soon as everything's figured out, this project may change heavily as well.
While we wait, I'll be only dealing with possible bugs. Thanks for understanding :]**

.. image:: https://travis-ci.org/lucianoratamero/django_apistar.svg?branch=master
    :target: https://travis-ci.org/lucianoratamero/django_apistar

This project is a `Django`_ App that switches between Django and `API
Star`_\ ’s routes and views. That way, we have API Star as the API
frontend, while leaving Django's toolset available for devs to
work with.

Both API Star’s docs and Django Admin work as intended.
You can see a Django + API Star implementation example at the django_apistar_example_ or test it on heroku_.

.. _django_apistar_example: https://github.com/lucianoratamero/django_apistar_example
.. _heroku: https://django-apistar-example.herokuapp.com/docs/

Suppports:

- django>=1.8
- apistar>=0.5.40
- python>=3.6,<3.7

Installation
~~~~~~~~~~~~
.. code:: shell

    pip install django_apistar


After installing, we need to add ``django_apistar`` to your ``INSTALLED_APPS`` in your project’s ``settings.py``:

.. code:: python

    INSTALLED_APPS = (
        ...
        'django_apistar',
        'your_api_star_app',
        ...
    )


Then, we need to set up three settings: a base API Star route module (``APISTAR_ROUTE_CONF``), API Star’s own settings and to change the default WSGI application:


.. code:: python

    APISTAR_SETTINGS = {
        'ALLOWED_DJANGO_ROUTES': ('/admin/', '/static/'),
    }

    APISTAR_ROUTE_CONF = 'your_api_star_app.routes'

    # remember that the following setting already exists in a default django settings file!
    WSGI_APPLICATION = 'django_apistar.wsgi.application'


The ``ALLOWED_DJANGO_ROUTES`` key describes which routes you want API Star to ignore. Only ``'/static/'`` is required, since we want Django to keep managing static files for us.

Now, if you want to run the dev server, run ``python manage.py runserver`` and hack away!


Authentication
~~~~~~~~~~~~~~

We support Basic and Token/Bearer authentication.

To use them, configure your ``APISTAR_SETTINGS`` as you would configure your API Star app:

.. code:: python

    from django_apistar.authentication.components import DjangoBasicAuthentication, DjangoTokenAuthentication

    ...

    APISTAR_SETTINGS['COMPONENTS'] = [DjangoBasicAuthentication(), DjangoTokenAuthentication()],

If you want to use authentication by token, you need to add the ``django_apistar.authentication`` to your ``INSTALLED_APPS``, then migrate your database.

.. code:: python

    INSTALLED_APPS = (
        ...
        'django_apistar',
        'django_apistar.authentication',
        'your_api_star_app',
        ...
    )

Token authentication views
''''''''''''''''''''''''''

We provide two helper views for token authentication. To set them up, add the routes into your root ``routes.py`` file:

.. code:: python

    from django_apistar.authentication import routes

    routes = [
        ...,
        Include('/auth', routes),
    ]

The views will be added to your ``/docs/``, as usual.

How it works
~~~~~~~~~~~~

This Django app contains a custom WSGI application that smartly changes between API Star's and Django's response handlers. By default, all requests will be responded by API Star, unless the ``ALLOWED_DJANGO_ROUTES`` settings key contains that route.

This way, we are able to bypass Django completely when responding API requests, while keeping Django ready to respond to more complicated requests, like Django Admin and complex template/form views.

Another big advantage is that this app enables both Django Admin **and** API Star automatic API docs.

Implementing views
''''''''''''''''''

There is no need to think about corner cases when writing views. We only need to keep in mind that we won’t be able to use the ``django_orm`` backend baked into API Star, so we must access models directly to deal with CRUD operations.

For example, let’s create a view that persists a ``Product``:

.. code:: python

    from core import schemas
    from core import models

    def create_product(product: schemas.Product) -> schemas.Product:
        db_product = models.Product(**product)
        db_product.save()
        return http.JSONResponse(schemas.Product(db_product.__dict__), status_code=201)

As intended, all the data validation is at the schemas, and everything is handled gracefully by API Star.

Implementing tests
''''''''''''''''''

To test your API Star views, we provide a hybrid ``TestClient`` that is API Star aware and a custom TestCase, leveraging Django's own ``TestCase`` by including the ``reverse_url`` method from API Star's router:

.. code:: python

    from django_apistar.test import TestCase #  our custom TestCase
    from model_mommy import mommy

    from core import models, schemas


    class TestListProducts(TestCase):

        def test_list_products(self):
            '''
            The reverse_url method behaves exactly like Django's reverse,
            but uses the view's defined name as namespace.
            The builtin client is based on the API Star Test Client,
            so it's preferred to use this test case only to test API Star's views.
            '''

            url = self.reverse_url('list_products')
            db_product = mommy.make(models.Product, rating=5, size='large')

            response = self.client.get(url)
            content = response.json()

            expected_product = schemas.Product(db_product.__dict__)
            self.assertEqual(1, len(content))
            self.assertEqual(expected_product, content[0])

Performance
~~~~~~~~~~~

Since we capture the request at the WSGI level, you should expect no drops in performance whatsoever.

I've made a few (and completely arbitrary) benchmarks. I've used Siege and set up two views, one Django view, one API Star view, both only responding a json response with ``{"message": "Hello, World!"}``. These were all run in my computer, so don't expect true results - this is only for you to have an idea.

+---------------------+-----------+-----------+-----------+-----------+----------------+
|                     | apistar   | django2   | django2-no middlewares| django_apistar |
+=====================+===========+===========+=======================+================+
| transactions        | 13688     | 6840      | 10507                 |  13899         |
+---------------------+-----------+-----------+-----------------------+----------------+
| transactions/sec    | 1482.99   | 716.23    | 1085.43               |1440.31         |
+---------------------+-----------+-----------+-----------------------+----------------+
| longest transaction | 0.08 sec  | 3.06      | 3.24                  |    0.08        |
+---------------------+-----------+-----------+-----------------------+----------------+

Contributing
~~~~~~~~~~~~

There are still a lot of ways we can improve and add more features to this app. If you find any bugs or have significant suggestions, just open an issue or contact me at luciano@ratamero.com. Pull requests will be received with all care and attention as well :)

.. _Django: https://www.djangoproject.com/
.. _API Star: https://github.com/encode/apistar


Changelog
~~~~~~~~~~~~

0.5.40__0
'''''''''
- updates API Star version and code references;
- refactor classes into components;
- adds sample event hook for authentication.

0.3.9__0
''''''''
- starts using matching versions with API Star to simplify things (0.3.9__x will always work and depend on apistar==0.3.9);
- locks maximum API Star version to 0.3.9.

0.3.2
'''''
- adds authentication app;
- adds views, models, schemas and authenticators for token authentication.

0.3.1
'''''
- fixes default ``DJANGO_SETTINGS_MODULE``;
- sets up Django before starting the WSGI application, enabling use with Heroku.

0.3.0
'''''
- removes the middleware implementation in favor of a custom WSGI app;
- removes templates folder and ``apps.py``, since they won't be necessary anymore;
- adds custom TestClient and TestCase to the ``tests`` module;
- improves performance by ~100% by bypassing Django when answering API Star's requests.

0.2.3
'''''
- coupled API Star to Django via middlewares;
- hijacks Django's WSGI process to respond using API Star's views.
