from functools import partial

from django.contrib.auth import REDIRECT_FIELD_NAME

from arcutils.settings import make_prefixed_get_setting


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


get_setting = make_prefixed_get_setting('MASQUERADE', DEFAULTS)


# Convenience functions for getting often-used settings

is_enabled = partial(get_setting, 'enabled', False)
get_param_name = partial(get_setting, 'param_name')
get_redirect_field_name = partial(get_setting, 'redirect_field_name', REDIRECT_FIELD_NAME)
get_session_key = partial(get_setting, 'session_key')
get_user_attr = partial(get_setting, 'user_attr')
