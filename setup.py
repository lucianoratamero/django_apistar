from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='django_apistar',
    version='0.5.40__0',
    description='Django app for using API Star as frontend.',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/lucianoratamero/django_apistar',
    author='Luciano Ratamero',
    author_email='luciano@ratamero.com',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 2.0',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
    ],

    include_package_data=True,
    keywords='apistar api rest django',
    packages=find_packages(exclude=['tests']),
    install_requires=['django>=1.8', 'apistar>=0.4.0'],
    python_requires='>=3.6,<3.7',
)
