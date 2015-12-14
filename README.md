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
            'search_base': 'ou=people,dc=pdx,dc=edu',
            'tls': {
                'ca_certs_file': '/path/to/ca_file.crt',
            }
        }
    }

## Features

1. `arcutils.will_be_deleted_with(obj)` yields a two tuple -- a model class, and a set of objects
   -- that would be deleted if obj were deleted. This is useful on your delete views so you can
   list the objects that will be deleted in a cascading manner.
1. `arcutils.ChoiceEnum`

        class FooType(ChoiceEnum):

            A = 1
            B = 2

        class SomeModel(models.Model):

            foo = models.ChoiceField(choices=FooType.as_choices())

1. `arcutils.dictfetchall` pass a cursor, and get the rows back as a dict
1. `arcutils.ldap.ldapsearch(query, using='default', **kwargs)` performs an LDAP search using the
   LDAP connection specified by the using parameter. By default, each LDAP result is parsed into
   a "profile", which is just a dict with user info pulled from the LDAP attributes:

        results = ldapsearch('(uid=mdj2)')
        print(results[0])  # -> {'first_name': 'Matt', 'last_name': 'Johnson', ...}
        

1. `arcutils.BaseFormSet` and `arcutils.BaseModelFormSet` have an iter_with_empty_form_first() that
   is is basically `([formset.empty_form] + formset.forms)`. This makes it convenient to iterate
   over the empty form in templates, without having a special case for it.
1. `arcutils.BaseFormSet` and `arcutils.BaseModelFormSet` override the clean method, so that if
   a form is being deleted, its validation errors are blanked out.
1. Console script: some ARCUtils functionality can be accessed via the `arcutils` console script
   (or via `python -m arcutils`). Currently, there is one subcommand for running LDAP queries:
   
        arcutils ldap '(uid=wbaldwin)'

## Testing

    pip install -e .[dev]
    ./runtests.py
