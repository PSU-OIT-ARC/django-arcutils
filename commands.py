from runcommands import command
from runcommands.commands import show_config  # noqa: F401
from runcommands.util import abort

from arctasks.base import install, lint  # noqa: F401
from arctasks.python import show_upgraded_packages  # noqa: F401
from arctasks.release import *  # noqa: F401,F403


@command
def test(config, tests=(), fail_fast=False, verbosity=1, with_coverage=False, with_lint=False):
    from coverage import Coverage

    from django import setup
    from django.conf import settings
    from django.conf.urls import url
    from django.http import HttpResponse
    from django.test.runner import DiscoverRunner

    with_coverage = with_coverage and not tests
    with_lint = with_lint and not tests

    settings.configure(
        DEBUG=True,
        ALLOWED_HOSTS=['*'],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
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
    runner = DiscoverRunner(failfast=fail_fast, verbosity=verbosity)

    if with_coverage:
        coverage = Coverage(source=['arcutils'])
        coverage.start()

    if tests:
        num_errors = runner.run_tests(tests)
    else:
        num_errors = runner.run_tests(['arcutils'])

    if num_errors:
        abort(code=num_errors, message='Test failure(s) encountered; aborting')

    if with_coverage:
        coverage.stop()
        coverage.report()

    if with_lint:
        lint(config)
