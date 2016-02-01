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
def _is_internal_ip_address(self, addr):
    addr = ipaddress.ip_address(addr)
    return addr.is_loopback or addr.is_private
INTERNAL_IPS = type('INTERNAL_IPS', (), dict(__contains__=_is_internal_ip_address))()


def init_settings(settings=None, local_settings=True, quiet=False, level=2):
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
        init_local_settings(settings, quiet)


def init_local_settings(settings, quiet):
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
    settings.update(load_and_check_settings(settings, quiet=quiet))


NOT_SET = object()


class SettingNotFoundError(Exception):

    pass


def get_setting(key, default=NOT_SET, _settings=None):
    """Get setting for ``key``, falling back to ``default`` if passed.

    ``key`` should be a string like 'ARC.cdn.hosts' or 'X.Y.0'. The key
    is split on dots into path segments, then the settings are traversed
    like this:

        - Set current value to django.conf.settings.{first segment}
        - For each other segment
            - Get current_value[segment] if current value is a dict
            - Get current_value[int(segment)] if current value is a list

    Only dicts, list, and tuples will be traversed. If a segment
    contains some other type of value, a ``ValueError`` will be raised.
    Note that we don't return the default in this case because this
    means an existing setting is being accessed incorrectly.

    If a non-int index is given for a list or tuple segment, this will
    also raise a ``ValueError``.

    If the setting isn't found, the ``default`` value will be returned
    if specified; otherwise, a ``SettingsNotFoundError`` will be raised.

    ``_settings`` can be used to inject a mock settings object in
    testing.

    """
    from django.conf import settings

    if _settings:
        settings = _settings

    root, *path = key.split('.')
    setting = getattr(settings, root, NOT_SET)

    for segment in path:
        if setting is NOT_SET:
            break
        if isinstance(setting, dict):
            setting = setting.get(segment, NOT_SET)
        elif isinstance(setting, (list, tuple)):
            index = int(segment)
            try:
                setting = setting[index]
            except IndexError:
                setting = NOT_SET
        else:
            raise ValueError('Cannot traverse into setting of type %s' % type(setting))

    if setting is NOT_SET:
        if default is NOT_SET:
            raise SettingNotFoundError('Could not find setting for key "%s"' % key)
        else:
            setting = default

    return setting


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
