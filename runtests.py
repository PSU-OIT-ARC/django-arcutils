#!/usr/bin/env python
import sys

from django import setup
from django.conf import settings
from django.conf.urls import url
from django.http import HttpResponse
from django.test.runner import DiscoverRunner

settings.configure(
    DEBUG=True,
    ALLOWED_HOSTS=['*'],
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
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
            ]
        }
    }],
)

setup()
test_runner = DiscoverRunner(verbosity=1)

failures = test_runner.run_tests(['arcutils'])
if failures:
    sys.exit(failures)
