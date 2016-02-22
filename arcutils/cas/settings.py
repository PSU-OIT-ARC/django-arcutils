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


NO_DEFAULT = object()


def get_setting(name, default=NO_DEFAULT):
    """Get CAS setting ``name``.

    Attempt to get the setting from:

    1. Project CAS settings
    2. ``default`` arg, if passed
    3. :global:`DEFAULTS`

    If ``name`` isn't found in the project's settings or in the global
    defaults and no fallback is passed via the ``default`` keyword arg,
    a :exc:`LookupError` will be raised.

    """
    cas_settings = getattr(settings, 'CAS', {})

    # Look in project settings or try falling back to passed default.
    value = cas_settings.get(name, default)

    # Setting not found in project and no fallback passed, so fall back
    # even further to global defaults.
    if value is NO_DEFAULT:
        value = DEFAULTS.get(name, default)

    # Setting not found anywhere; blow up.
    if value is NO_DEFAULT:
        raise LookupError('Missing CAS setting: %s' % name)

    return value
