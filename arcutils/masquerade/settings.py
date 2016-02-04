from functools import partial

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME

from arcutils.types import Some, Null


def get_settings():
    """Get masquerade settings.

    The first time this is called, the masquerade settings will be
    initialized with defaults. This also sort-of documents the settings
    that are available.

    """
    masquerade_settings = getattr(settings, 'MASQUERADE', {})
    if not masquerade_settings.get('_initialized', False):
        masquerade_settings.setdefault('enabled', False)
        masquerade_settings.setdefault('session_key', 'masquerade.user_id')
        masquerade_settings.setdefault('param_name', 'user_id')
        masquerade_settings.setdefault('can_masquerade', None)
        masquerade_settings.setdefault('can_masquerade_as', None)
        masquerade_settings.setdefault('default_redirect_url', '/')
        masquerade_settings.setdefault('user_attr', 'masquerade_info')
        masquerade_settings.setdefault('redirect_field_name', REDIRECT_FIELD_NAME)
        masquerade_settings['_initialized'] = True
    return masquerade_settings


def get_setting(name, default=None):
    """Get setting specified by ``name``.

    Fall back to ``default`` if the setting doesn't exist, unless
    ``default`` is ``Null``.

    Args:
        name: Masquerade setting name, sans ``MASQUERADE.`` prefix
        default: Value to use when the setting doesn't exist

    Returns:
        object: The value of the setting, or the default value if the
            setting does not exist

    Raises:
        KeyError: Setting doesn't exist and ``default`` is ``Null``

    """
    option = get_setting_as_option(name, default)
    value = option.unwrap(default=KeyError(name))
    return value


def get_setting_as_option(name, default=Null):
    """Return masquerade setting as an Option."""
    masquerade_settings = get_settings()
    value = masquerade_settings.get(name, default)
    return value if value is Null else Some(value)


# Convenience functions for getting often-used settings

is_enabled = partial(get_setting, 'enabled', False)
get_param_name = partial(get_setting, 'param_name', Null)
get_redirect_field_name = partial(get_setting, 'redirect_field_name', REDIRECT_FIELD_NAME)
get_session_key = partial(get_setting, 'session_key', Null)
get_user_attr = partial(get_setting, 'user_attr', Null)
