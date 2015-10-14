# ARC Utils

[![Build Status](https://travis-ci.org/PSU-OIT-ARC/django-arcutils.svg?branch=master)](https://travis-ci.org/PSU-OIT-ARC/django-arcutils)

This package provides utilities that are commonly needed in ARC Django projects. It supports Python
3.3+ and Django 1.7+.

## Development

To work on this package, run `make init`; this will create a virtualenv for you, install the
package in editable mode, and run the tests. Take a look at the Makefile to see the actual commands
that are run.

## Usage

_The following assumes your package has a setup.py that uses setuptools' `setup()` and that you are
using pip. You will need to specify `--find-links http://cdn.research.pdx.edu/pypi/dist/` when
running `pip install` (it's easiest to add `--find-links ...` to the top of the project's
requirements.txt)._

To use this package in a Django project, do the following:

- Add `'django-arcutils'` to `install_requires` in setup.py
- To use the LDAP features, add `'django-arcutils[ldap]'` to `install_requires`
- To use template tags, add `'arcutils'` to `INSTALLED_APPS`

Optionally, add your LDAP connection information:

    LDAP = {
        'default': {
            'host': 'ldap://ldap-bulk.oit.pdx.edu',
            'username': 'rethinkwebsite,ou=service,dc=pdx,dc=edu',
            'password': 'foobar',
            'search_dn': 'ou=people,dc=pdx,dc=edu',
            'ca_file': '/path/to/ca_file.crt',
        }
    }

## Features

1. Adds all arcutils template tags to the builtin template tags
1. `arcutils.will_be_deleted_with(obj)` yields a two tuple -- a model class, and a set of objects
   -- that would be deleted if obj were deleted. This is useful on your delete views so you can
   list the objects that will be deleted in a cascading manner.
1. `arcutils.ChoiceEnum`

        class FooType(ChoiceEnum):

            A = 1
            B = 2

            _choices = (
                (A, 'Alpha'),
                (B, 'Beta'),
            )

        class SomeModel(models.Model):

            foo = models.ChoiceField(choices=FooType)

1. `arcutils.dictfetchall` pass a cursor, and get the rows back as a dict
1. `arcutils.ldap.ldapsearch(query, using='default', **kwargs)` performs an LDAP search using the
   LDAP connection specified by the using parameter.
1. `arcutils.ldap.parse_profile()` will parse out the first_name, last_name, email, and odin as
   a dict from an ldap result.

        results = ldapsearch('odin=mdj2')
        dn, entry = results[0]
        parse_profile(entry)

1. `arcutils.BaseFormSet` and `arcutils.BaseModelFormSet` have an iter_with_empty_form_first() that
   is is basically `([formset.empty_form] + formset.forms)`. This makes it convenient to iterate
   over the empty form in templates, without having a special case for it.
1. `arcutils.BaseFormSet` and `arcutils.BaseModelFormSet` override the clean method, so that if
   a form is being deleted, its validation errors are blanked out.

### Logging

`arcutils.logging.basic` configures basic logging to the console, and pipes logs to
`LOGSTASH_ADDRESS` using the logstash-forwarder protocol when DEBUG is off. Add `LOGGING_CONFIG
= 'arcutils.logging.basic'` to use. Set the `LOGSTASH_ADDRESS` to something like 'localhost:5000'
during development. It defaults to 'logs.rc.pdx.edu:5043'. The logstash-forwarder protocol requires
SSL, so you must specify the path to a CA file using the `LOGSTASH_CA_CERTS` setting. This package
includes the PSUCA.crt file, which is the default.

`arcutils.logging.basic` also configures error email logging; for this to work, the `SERVER_EMAIL`
setting *must* be set to a valid value.

## Testing

    pip install -e .[dev]
    ./runtests.py
