import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

try:
    # Django 1.8
    from django.core.exceptions import FieldDoesNotExist
except ImportError:
    # Django 1.7
    from django.db.models.fields import FieldDoesNotExist


log = logging.getLogger(__name__)


def get_or_create_user(cas_data):
    """If user does not exist, create from CAS response data.

    ``cas_data`` must contain a 'username' key. It may also contain
    other user attributes, which will be set when creating a user
    (attributes that don't correspond to fields on the user model will
    be ignored).

    This is called by the CAS auth back end if authentication is
    successful. If the corresponding user already exists, it will be
    returned as is; if it doesn't, a new user record will be created
    and returned.

    This attempts to populate some user attributes from the CAS
    response: ``first_name``, ``last_name``, and ``email``. If any of
    those attributes aren't found in the CAS response, they won't be
    set on the new user object; an error isn't raised because those
    attributes aren't critical and can be set later.

    The user's password is set to something unusable in the app's user
    table--i.e., we don't store passwords for CAS users in the app.

    """
    user_model = get_user_model()
    username = cas_data['username']

    try:
        user = user_model.objects.get(username=username)
    except user_model.DoesNotExist:
        pass
    else:
        return user

    # These defaults may be overridden by ``data``.
    user_args = {
        'email': '{username}@pdx.edu'.format(username=username),
    }

    for name, value in cas_data.items():
        try:
            user_model._meta.get_field(name)
        except FieldDoesNotExist:
            pass
        else:
            user_args[name] = value

    is_superuser = username in getattr(settings, 'SUPERUSERS', ())
    is_staff = username in getattr(settings, 'STAFF', ())
    is_staff = is_staff or is_superuser

    user_args.update({
        'password': make_password(None),
        'is_staff': is_staff,
        'is_superuser': is_superuser,
    })

    user = user_model.objects.create(**user_args)
    return user


default_response_callback = get_or_create_user
