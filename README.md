# ARC Utils

## Install

    pip install -e git://github.com/PSU-OIT-ARC/django-arcutils.git#egg=django-arcutils
    
Add to settings file:
    
    INSTALLED_APPS = (
        'arcutils',
    )

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


## Testing

    pip install model_mommy django django-bootstrap-form
    ./runtests.py
