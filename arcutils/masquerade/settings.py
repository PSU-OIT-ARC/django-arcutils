from functools import partial

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME


NO_DEFAULT = object()


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
    ``strict`` is set (a ``KeyError`` will be raised in this case).

    """
    masquerade_settings = get_settings()
    if default is NO_DEFAULT:
        return masquerade_settings[name]
    return masquerade_settings.get(name, default)


# Convenience functions for getting often-used settings

is_enabled = partial(get_setting, 'enabled', False)
get_param_name = partial(get_setting, 'param_name', NO_DEFAULT)
get_redirect_field_name = partial(get_setting, 'redirect_field_name', REDIRECT_FIELD_NAME)
get_session_key = partial(get_setting, 'session_key', NO_DEFAULT)
get_user_attr = partial(get_setting, 'user_attr', NO_DEFAULT)
