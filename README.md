# ARC Utils

[![Build Status](https://travis-ci.org/PSU-OIT-ARC/django-arcutils.svg?branch=1.x-maint)](https://travis-ci.org/PSU-OIT-ARC/django-arcutils)

This package provides utilities that are commonly needed in ARC Django
projects. It supports Python & Django versions:

- Python 2.6: Django 1.6
- Python 2.7: Django 1.7 & 1.8
- Python 3.3: Django 1.7 & 1.8

## Deprecation Notice

The 1.x version of ARCUtils is deprecated. New projects should use
version 2. Projects using 1.x should upgrade to version 2 as soon as
possible, assuming it's practical to do so (e.g., projects that aren't
in active development shouldn't be proactively upgraded).

## Development

To work on this package, run `make init`; this will create a Python
2 virtualenv for you, install the package in editable mode, and run the
tests. Take a look at the Makefile to see the actual commands that are
run.

## Testing

Run `make test`.

## Usage

To use this package in a Django project, do the following:

- Add `-f http://cdn.research.pdx.edu/pypi/dist/` to the top of the
  project's `requirements.txt` (this is required in all cases)
- If the project is set up as a distutils/setuptools package (i.e., it
  has a `setup.py`):
  - Add `django-arcutils>=1.x,<2.0` to `install_requires`
  - To use the LDAP features, add `django-arcutils>=1.x,<2.0[ldap]` to
    `install_requires` instead
- If the project is not a distutils/setuptools package:
  - Add the django-arcutils dependencies to the project's
    `requirements.txt` instead of `install_requires`
- Add `arcutils` to `INSTALLED_APPS`

NOTE: The `1.x` in the requirements above will need to be replaced with
      a concrete version like `1.1.1`. The `<2.0` part is also very
      important; without it, the latest 2.x version will be installed,
      which _won't work_ for projects that are currently using version
      1.x.

In **Django 1.6 and worse** you must add this after Django apps have
been loaded (for example, in a models.py file):

    from arcutils.apps import ARCUtilsConfig
    ARCUtilsConfig().ready()


Optionally, add your LDAP connection information

    LDAP = {
        "default": {
            "host": "ldap://ldap-bulk.oit.pdx.edu",
            "username": "rethinkwebsite,ou=service,dc=pdx,dc=edu",
            "password": "foobar",
            "search_dn": "ou=people,dc=pdx,dc=edu",
            "ca_file": "/path/to/ca_file.crt",
        }
    }


## Features

1. Monkey Patch `django.contrib.auth.forms.PasswordResetForm` so that it raises an error if the email address is not found in the DB
1. Adds the `bootstrap` template tag and all arcutils template tags to the builtin template tags
1. `arcutils.will_be_deleted_with(obj)` yields a two tuple -- a model class, and a set of objects -- that would be deleted if obj were deleted. This is useful on your delete views so you can list the objects that will be deleted in a cascading manner.
1. `arcutils.ChoiceEnum`
```python
class FooType(ChoiceEnum):
    A = 1
    B = 2

    _choices = (
        (A, "Alpha"),
        (B, "Beta"),
    )

# in your model somewhere

class SomeModel(models.Model):
    foo = models.ChoiceField(choices=FooType)

```
1. `arcutils.dictfetchall` pass a cursor, and get the rows back as a dict
1. `arcutils.ldap.escape` is an alias for `ldap.filter.escape_filter_chars`
1. `arcutils.ldap.ldapsearch(query, using='default', **kwargs)` performs an LDAP search using the LDAP connection specified by the using parameter.
1. `arcutils.ldap.parse_profile()` will parse out the first_name, last_name, email, and odin as a dict from an ldap result.
```python
results = ldapsearch("odin=mdj2")
dn, entry = results[0]
parse_profile(entry)
```
1. `arcutils.BaseFormSet` and `arcutils.BaseModelFormSet` have an iter_with_empty_form_first() that is is basically `([formset.empty_form] + formset.forms)`. This makes it convenient to iterate over the empty form in templates, without having a special case for it.
1. `arcutils.BaseFormSet` and `arcutils.BaseModelFormSet` override the clean method, so that if a form is being deleted, its validation errors are blanked out.
1. arcutils will clear expired sessions after `CLEAR_EXPIRED_SESSIONS_AFTER_N_REQUESTS` requests.
   The default is 100 requests. `CLEAR_EXPIRED_SESSIONS_AFTER_N_REQUESTS` can be set to `None` to
   disable this feature. Note: the implementation is probabilistic, so there's no guarantee that
   expired sessions will be cleared after exactly N requests.

### Logging

`arcutils.logging.basic` configures basic logging to the console, and pipes
logs to `LOGSTASH_ADDRESS` using the logstash-forwarder protocol when DEBUG is
off. Add `LOGGING_CONFIG = 'arcutils.logging.basic'` to use. Set the
`LOGSTASH_ADDRESS` to something like 'localhost:5000' during development. It
defaults to 'logs.rc.pdx.edu:5043'. The logstash-forwarder protocol requires
SSL, so you must specify the path to a CA file using the `LOGSTASH_CA_CERTS`
setting. This package includes the PSUCA.crt file, which is the default.

`arcutils.logging.basic` also configures error email logging; for this to work, the `SERVER_EMAIL`
setting *must* be set to a valid value.
