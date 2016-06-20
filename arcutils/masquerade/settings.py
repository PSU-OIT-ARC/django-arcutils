from functools import partial

from django.contrib.auth import REDIRECT_FIELD_NAME

from arcutils.settings import PrefixedSettings


DEFAULTS = {
    'enabled': False,
    'session_key': 'masquerade.user_id',
    'param_name': 'user_id',
    'can_masquerade': None,
    'can_masquerade_as': None,
    'default_redirect_url': '/',
    'user_attr': 'masquerade_info',
    'redirect_field_name': REDIRECT_FIELD_NAME,
}


settings = PrefixedSettings('MASQUERADE', DEFAULTS)


# Convenience functions for getting often-used settings

is_enabled = partial(settings.get, 'enabled', False)
get_param_name = partial(settings.get, 'param_name')
get_redirect_field_name = partial(settings.get, 'redirect_field_name', REDIRECT_FIELD_NAME)
get_session_key = partial(settings.get, 'session_key')
get_user_attr = partial(settings.get, 'user_attr')
