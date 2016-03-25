import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import FieldDoesNotExist

from arcutils.exc import ARCUtilsDeprecationWarning


log = logging.getLogger(__name__)


def get_or_create_user(cas_data):
    ARCUtilsDeprecationWarning.warn('This function is deprecated.')

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
