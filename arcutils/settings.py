"""Utilities for setting up a project's settings.

The default way to use this is to import and call :func:`init_settings`
in a project's settings module:

    # project/top_level_package/settings.py
    from arcutils.settings import init_settings
    init_settings()

This adds a few default settings for bootstrapping purposes and then
loads the project's local settings--the django-local-settings variety.

Pass ``local_settings=False`` to :func:`init_settings` if the project
doesn't use django-local-settings.

"""
import base64
import inspect
import ipaddress
import os
import pkg_resources

from local_settings import NO_DEFAULT, load_and_check_settings, LocalSetting, SecretSetting


ARCUTILS_PACKAGE_DIR = pkg_resources.resource_filename('arcutils', '')


# Considers any standard private IP address a valid internal IP address
INTERNAL_IPS = type('INTERNAL_IPS', (), {
    '__contains__': lambda self, addr: ipaddress.ip_address(addr).is_private,
})()


def init_settings(settings=None, local_settings=True, level=2):
    """Initialize settings.

    Call this from the global scope of your project's settings module::

        from arcutils.settings import init_settings
        init_settings()

    It will add a few default settings that are commonly used in local
    settings files:

        - ARCUTILS_PACKAGE_DIR
        - PACKAGE (top level project package)
        - PACKAGE_DIR (top level project package directory)

    The ``PACKAGE`` and ``PACKAGE_DIR`` settings will be computed
    dynamically (based on the location of the settings module this
    function is called from). If this isn't working, you can set the
    ``PACKAGE`` setting explicitly in the project's settings (before
    calling this function)::

        PACKAGE = 'quickticket'
        init_settings()

    Generally, you won't need to pass ``settings``, but if you do, it
    should be a dict of settings as you'd get from calling ``globals()``
    in the project's settings module.

    """
    settings = settings if settings is not None else get_settings(level)
    settings.setdefault('ARCUTILS_PACKAGE_DIR', ARCUTILS_PACKAGE_DIR)
    package = settings.setdefault('PACKAGE', derive_top_level_package_name(level=level))
    settings.setdefault('PACKAGE_DIR', pkg_resources.resource_filename(package, ''))
    if local_settings:
        init_local_settings(settings)


def init_local_settings(settings):
    default_secret_key = base64.b64encode(os.urandom(64)).decode('utf-8')
    defaults = {
        'DEBUG': LocalSetting(False),
        'SECRET_KEY': SecretSetting(default_secret_key),
        'DATABASES': {
            'default': {
                'ENGINE': LocalSetting('django.db.backends.postgresql_psycopg2'),
                'NAME': LocalSetting(settings.get('PACKAGE', NO_DEFAULT)),
                'USER': LocalSetting(''),
                'PASSWORD': SecretSetting(),
                'HOST': LocalSetting(''),
            },
        },
    }
    for k, v in defaults.items():
        settings.setdefault(k, v)
    settings.update(load_and_check_settings(settings))


# Internal helper functions


def derive_top_level_package_name(level=1):
    """Return top level package based on location of settings module.

    This assumes the project is structured like so, with the settings
    module in the top level package::

        {package}/
            __init__.py
            settings.py

    Further, it's assumed that this function is being called from the
    global scope of the settings module.

    If the settings module is in a sub-package (or if this is being
    called from within a function), the ``level`` arg can be adjusted
    accordingly. For example, for a project structured like this,
    ``level`` would be set to 2::

        {package}/
            __init__.py
            settings/
                settings.py

    The ``level`` arg can be thought of as "levels deep" in terms of
    both packages and functions.

    """
    frame = inspect.stack()[level][0]
    package = frame.f_globals['__package__']
    return package


def get_settings(level=2):
    """Get module globals."""
    frame = inspect.stack()[level][0]
    return frame.f_globals
