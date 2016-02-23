from django.conf import settings


DEFAULTS = {
    'base_url': 'https://sso.pdx.edu/idp/profile/cas/',
    'login_path': 'login',
    'logout_path': '/idp/profile/Logout',
    'validate_path': 'serviceValidate',
    'redirect_url': None,
    'auto_create_user': True,
    'logout_completely': True,
    'session_key.redirect_to': 'CAS.redirect_to',
    'response_callbacks': ['arcutils.cas.callbacks.default_response_callback'],
}


NOT_SET = object()


def get_setting(key, default=NOT_SET):
    """Get a CAS setting.

    Attempt to get the setting from:

    1. Project CAS settings
    2. :global:`DEFAULTS`
    3. ``default`` arg

    If the setting isn't found in the project's settings or in the
    defaults and no fallback is passed via the ``default`` keyword arg,
    a :exc:`LookupError` will be raised.

    """
    cas_settings = getattr(settings, 'CAS', {})

    try:
        return cas_settings[key]
    except KeyError:
        return DEFAULTS.get(key, default)

    if value is NOT_SET:
        raise LookupError('Could not find CAS setting for key "%s"' % key)

    return value
