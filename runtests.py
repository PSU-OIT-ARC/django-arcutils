#!/usr/bin/env python
import sys

from django import setup
from django.conf import settings
from django.conf.urls import url
from django.http import HttpResponse
from django.test.runner import DiscoverRunner
from django.test.utils import setup_test_environment

settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    ROOT_URLCONF=(
        url(r'^test$', lambda request: HttpResponse('test'), name='test'),
    ),
    INSTALLED_APPS=(
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'arcutils',
    ),
    MIDDLEWARE_CLASSES=[],
    LDAP={
        'default': {
            'host': 'ldap://ldap-login.oit.pdx.edu',
            'username': '',
            'password': '',
            'search_base': 'ou=people,dc=pdx,dc=edu',
        }
    },
)

setup()
setup_test_environment()
test_runner = DiscoverRunner(verbosity=1)

failures = test_runner.run_tests(['arcutils'])
if failures:
    sys.exit(failures)
