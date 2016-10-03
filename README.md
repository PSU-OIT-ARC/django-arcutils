# ARCUtils

[![Build Status](https://travis-ci.org/PSU-OIT-ARC/django-arcutils.svg?branch=master)](https://travis-ci.org/PSU-OIT-ARC/django-arcutils)

This package provides utilities that are commonly needed in ARC Django projects. It supports Python
3.3+ and Django 1.8+.

## General Note

If ARCUtils contains a specific type of functionality that is needed in an ARC project, it is
generally preferable to use the ARCUtils functionality instead of another package, since the entire
purpose of ARCUtils is to encapsulate the configuration and functionality needed by many or most
ARC projects.

On the other hand (and this is a note to self as much as to anyone else), we should _avoid_ adding
functionality to ARCUtils whenever possible.

## Development

To work on this package, run `make init`; this will create a virtualenv for you, install the
package in editable mode, and run the tests. Take a look at the Makefile to see the actual commands
that are run.

## Testing

Run `make test`.

## Usage

_The following assumes your package has a setup.py that uses setuptools' `setup()` and that you are
using pip. You will need to specify `--find-links http://cdn.research.pdx.edu/pypi/dist/` when
running `pip install` (it's easiest to add `--find-links ...` to the top of the project's
requirements.txt)._

To use this package in a Django project, do the following:

- Add `'django-arcutils'` to `install_requires` in setup.py
- To use the LDAP features, add `'django-arcutils[ldap]'` to `install_requires`
- To use template tags, add `'arcutils'` to `INSTALLED_APPS`

## Features

NOTE: Many features have not been documented yet :( To get an idea of all the available features,
take a look at the modules and packages in the top level `arcutils` directory.

### Console Script

Some ARCUtils functionality can be accessed via the `arcutils` console script (or via
`python -m arcutils`). Currently, there is one subcommand for running LDAP queries:

        arcutils ldap '(uid=pants)'

### CAS - arcutils.cas

CAS is used when a project needs to log users in with their PSU accounts. The basic setup is
straightforward:

- Add `"arcutils.cas.backends.CASModelBackend"` to the project's `AUTHENTICATION_BACKENDS` (in most
  cases, this will be the only value in `AUTHENTICATION_BACKENDS`)
- Include CAS URLs in the project's root URLconf: `url(r'^account/', include(arcutils.cas.urls))`

By default, the first time a user logs in, a `User` record (with no password) will be created in the
project's database.

### Database - arcutils.db

- `ChoiceEnum`

        class FooType(ChoiceEnum):

            A = 1
            B = 2

        class SomeModel(models.Model):

            foo = models.ChoiceField(choices=FooType.as_choices())

- `will_be_deleted_with(obj)` returns 2-tuples of
  `(model class of objects in set, set of objects that will be deleted along with obj)`. This can
  be used in delete views to list the objects that will be deleted in a cascading manner.

- `arcutils.db.dictfetchall`: pass a cursor and get the rows back as a dict

### Forms - arcutils.forms

- `arcutils.forms.BaseFormSet` and `arcutils.forms.BaseModelFormSet` have an
  `iter_with_empty_form_first()` method that is is basically
  `([formset.empty_form] + formset.forms)`. This makes it convenient to iterate over the empty form
  in templates without having a special case for it.

- `arcutils.forms.BaseFormSet` and `arcutils.forms.BaseModelFormSet` override the `clean` method
  so that if a form is being deleted, its validation errors are blanked out.

### LDAP - arcutils.ldap

To use the LDAP features, you will need at least a minimal set of LDAP settings:

    LDAP = {
        'default': {
            'host': 'ldap://ldap-bulk.oit.pdx.edu',
            'search_base': 'ou=people,dc=pdx,dc=edu',
        }
    }

- `arcutils.ldap.ldapsearch(query, using='default', **kwargs)` performs an LDAP search using the
  LDAP connection specified by the using parameter. By default, each LDAP result is parsed into
  a "profile", which is just a dict with user info pulled from the LDAP attributes:

        results = ldapsearch('(uid=mdj2)')
        print(results[0])  # -> {'first_name': 'Matt', 'last_name': 'Johnson', ...}

### Settings - arcutils.settings

TODO: Write this section.


### Tasks - arcutils.tasks

Implements a simple daily task runner as an alternative to cron or Celery.
