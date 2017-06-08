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
from datetime import datetime

from django import VERSION as DJANGO_VERSION
from django.conf import settings as django_settings
from django.utils import timezone

from local_settings import NO_DEFAULT, load_and_check_settings, LocalSetting, SecretSetting
from local_settings.settings import DottedAccessDict, Settings as LocalSettings


class _InternalIPsType:

    """Used to construct a convenient INTERNAL_IPS setting for dev.

    An *instance* of this type considers any standard loopback or
    private IP address a valid internal IP address.

    """

    def __contains__(self, addr):
        addr = ipaddress.ip_address(addr)
        return addr.is_loopback or addr.is_private


INTERNAL_IPS = _InternalIPsType()


def init_settings(settings=None, local_settings=True, prompt=None, quiet=None, package_level=0,
                  stack_level=2, drop=(), settings_processors=()):
    """Initialize project settings.

    Basic Usage
    ===========

    By default, it's assumed that the project is structured like so,
    with the settings module in the top level package::

        project/
            package/
                __init__.py
                settings.py
            README
            setup.py

    It's also assumed that :func:`init_settings` will be called from the
    global scope of the project's settings module::

        # package/settings.py
        from arcutils.settings import init_settings
        init_settings()

    A few default settings that are commonly used in local settings
    files will be added (if not explicitly set before calling this
    function):

        - ARCUTILS_PACKAGE_DIR
        - PACKAGE (top level project package)
        - PACKAGE_DIR (top level project package directory)
        - ROOT_DIR (project directory; should only be used in dev)
        - START_TIME (current date/time; will be an "aware" UTC datetime
          object if the project has time zone support enabled)

    If the project has additional local settings, they must be defined
    *before* this function is called.

    Advanced Usage
    ==============

    Generally, you won't need to pass ``settings``, but if you do, it
    should be a dict of settings as you'd get from calling ``globals()``
    in the project's settings module.

    If the settings module is in a sub-package, ``package_level`` will
    need to be adjusted accordingly. If :func:`init_settings` is being
    called from another function, ``stack_level`` will have to be
    adjusted accordingly. See :func:`derive_top_level_package_name` for
    more info about these args.

    The ``PACKAGE``, ``PACKAGE_DIR``, and ``ROOT_DIR`` settings will be
    derived based on the location of the settings module this function
    is called from. If this isn't working, ensure the ``package_level``
    and ``stack_level`` options are correct; or, set the ``PACKAGE``
    setting explicitly before calling this function::

        PACKAGE = 'quickticket'
        init_settings()

    ``PACKAGE_DIR`` and ``ROOT_DIR`` can also be set explicitly if
    necessary.

    .. note:: If the package name and related settings can't be derived
        automatically, that indicates a bug in this function.

    To drop unused default settings, specify a list of such settings via
    the ``drop`` arg.

    To process settings in any custom manner needed, pass a list of
    functions via ``settings_processors``. Each processor will be passed
    the settings to be manipulated as necessary.

    """
    settings = settings if settings is not None else get_module_globals(stack_level)

    if not settings.get('ARCUTILS_PACKAGE_DIR'):
        arcutils_package_dir = pkg_resources.resource_filename('arcutils', '')
        settings['ARCUTILS_PACKAGE_DIR'] = arcutils_package_dir

    if not settings.get('PACKAGE'):
        # The default value for PACKAGE is derived by figuring out where
        # init_settings was called from in terms of package and scope.
        settings['PACKAGE'] = derive_top_level_package_name(package_level, stack_level)

    if not settings.get('PACKAGE_DIR'):
        # The default value for PACKAGE_DIR is simply the directory
        # corresponding to PACKAGE.
        settings['PACKAGE_DIR'] = pkg_resources.resource_filename(settings['PACKAGE'], '')

    if not settings.get('ROOT_DIR'):
        # The default value for ROOT_DIR is the directory N levels up
        # from PACKAGE_DIR, where N is equal to the package depth of the
        # top level package. Note that in most cases N is 1; it will be
        # greater than 1 when the top level package is contained in a
        # namespace package.
        package_depth = len(settings['PACKAGE'].split('.'))
        parts = os.path.split(settings['PACKAGE_DIR'])
        root_dir = os.path.join(*parts[:package_depth])
        settings['ROOT_DIR'] = root_dir

    if not settings.get('VERSION'):
        dist = pkg_resources.get_distribution(settings['PACKAGE'])
        settings['VERSION'] = dist.version

    if local_settings:
        init_local_settings(settings, prompt=prompt, quiet=quiet)

    # NOTE: We can't simply use Django's timezone.now() here because it
    #       accesses settings.USE_TZ, but at this point the settings
    #       may not be considered fully configured by Django, so we have
    #       to do this to avoid an ImproperlyConfigured exception.
    use_tz = settings.get('USE_TZ', False)
    now = datetime.utcnow().replace(tzinfo=timezone.utc) if use_tz else datetime.now()
    settings.setdefault('START_TIME', now)

    if not settings.get('UP_TIME'):

        class UpTime:

            __slots__ = ('start_time',)

            def __init__(self, start_time):
                self.start_time = start_time

            @property
            def current(self):
                from django.utils import timezone
                return timezone.now() - self.start_time

        settings['UP_TIME'] = UpTime(settings['START_TIME'])

    # Remove the MIDDLEWARE_CLASSES setting on Django >= 1.10, but only
    # if the MIDDLEWARE setting is present *and* set.
    if DJANGO_VERSION[:2] >= (1, 10):
        if settings.get('MIDDLEWARE'):
            settings.pop('MIDDLEWARE_CLASSES', None)

    # Drop irrelevant settings.
    for name in drop:
        del settings[name]

    for processor in settings_processors:
        processor(settings)

    return settings


def init_local_settings(settings, prompt=None, quiet=None):
    """Initialize the local settings defined in ``settings``.

    Args:
        settings (dict): A dict of settings as you'd get from calling
            ``globals()`` in a Django settings module.
        quiet (bool): Squelch standard out when loading local settings.

    .. note:: If your project has additional local settings, they must
        be defined *before* this function is called.

    """
    suggested_secret_key = base64.b64encode(os.urandom(64)).decode('utf-8')
    defaults = {
        'DEBUG': LocalSetting(False),
        'ADMINS': LocalSetting([]),
        'ALLOWED_HOSTS': LocalSetting([]),
        'GOOGLE': {
            'analytics': {
                'tracking_id': LocalSetting(
                    None, doc='Enter Google Analytics tracking ID (UA-NNNNNNNN-N)'
                ),
            },
        },
        'MANAGERS': LocalSetting([]),
        'SECRET_KEY': SecretSetting(doc='Suggested: "{suggested_secret_key}"'.format(**locals())),
        'DATABASES': {
            'default': {
                'ENGINE': LocalSetting('django.db.backends.postgresql'),
                'NAME': LocalSetting(settings.get('PACKAGE', NO_DEFAULT)),
                'USER': LocalSetting(''),
                'PASSWORD': SecretSetting(),
                'HOST': LocalSetting(''),
            },
        },
    }
    for k, v in defaults.items():
        settings.setdefault(k, v)
    settings.update(load_and_check_settings(settings, prompt=prompt, quiet=quiet))


def get_setting(name, default=NO_DEFAULT, settings=None):
    """Get setting for ``name``, falling back to ``default`` if passed.

    ``name`` should be a string like 'ARC.cdn.hosts' or 'X.Y.0'. The
    name is split on dots into path segments, then the settings are
    traversed like this:

        - Set current value to django.conf.settings.{first segment}
        - For each other segment
            - Get current_value[segment] if current value is a dict
            - Get current_value[int(segment)] if current value is a list

    If the setting isn't found, the ``default`` value will be returned
    if specified; otherwise, a ``KeyError`` will be raised.

    ``settings`` can be used to retrieve the setting from a settings
     object other than the default ``django.conf.settings``.

    :class:`local_settings.settings.DottedAccessDict` is used to
    implement this functionality. See the django-local-settings project
    for more details about settings traversal.

    """
    if settings is None:
        settings = django_settings

    if not isinstance(settings, LocalSettings):
        settings = DottedAccessDict(get_settings_dict(settings))

    return settings.get_dotted(name, default)


class PrefixedSettings:

    """Read-only settings for a given ``prefix``.

    Args:
        prefix: An upper case setting name such as "CAS" or "LDAP"
        defaults: A dict of defaults for the prefix

    The idea is to make it easy to fetch sub-settings within a given
    package.

    For example::

        >>> DEFAULT_CAS_SETTINGS = {
        ...     'base_url': 'https://example.com/cas/',
        ...     # plus a bunch more CAS settings...
        ... }
        >>> cas_settings = PrefixedSettings('CAS', DEFAULT_CAS_SETTINGS)
        >>> cas_settings.get('base_url')
        'https://example.com/cas/'
        >>> cas_settings.get('logout_path', default='/default/logout/path')
        '/default/logout/path'

    See the ``cas``, ``ldap``, and ``masquerade`` packages for concrete
    examples of how this is used.

    """

    def __init__(self, prefix, defaults=None, settings=None):
        defaults = get_settings_dict(defaults)
        settings = get_settings_dict(settings if settings is not None else django_settings)
        self.__prefix = prefix
        self.__defaults = DottedAccessDict(defaults)
        self.__settings = DottedAccessDict(settings)

    def get(self, name, default=NO_DEFAULT):
        """Get setting for configured ``prefix``.

        Args:
            name: setting name without ``prefix``
            default: value to use if setting isn't present in the
                project's settings or in the ``defaults``

        Returns:
            object: Value of setting

                Attempt to get setting from:

                1. Project settings for ``prefix``
                2. Default settings from ``defaults``
                3. ``default`` arg

        Raises:
            KeyError: When the setting isn't found in the project's
                settings or in the ``defaults`` and no fallback is
                passed via the ``default`` keyword arg

        """
        qualified_name = '{prefix}.{name}'.format(prefix=self.__prefix, name=name)
        try:
            return self.__settings.get_dotted(qualified_name)
        except KeyError:
            return self.__defaults.get_dotted(name, default=default)

    def __getitem__(self, key):
        return PrefixedSettings.get(self, key, NO_DEFAULT)


# Internal helper functions


def get_settings_dict(settings):
    """For a given settings object, return a dict.

    Args:
        settings (object): Usually either a Django settings object or
            a dict; can also be a sequence that can be converted to
            a dict or some other non-dict mapping

    Returns:
        empty dict: ``settings`` is ``None``
        vars(settings._wrapped): ``settings`` is (or appears to be)
            a Django settings object
        dict(settings): ``settings`` is any other type of object

    """
    if settings is None:
        return {}
    if hasattr(settings, '_wrapped'):
        # A Django settings object
        # TODO: Find a better way to check for Django settings?
        return vars(settings._wrapped)
    return dict(settings)


def derive_top_level_package_name(package_level=0, stack_level=1):
    """Return top level package name.

    Args:
        package_level (int): How many package levels down the caller
            is. 0 indicates this function is being called from the top
            level package, 1 indicates that it's being called from a
            sub-package, etc.
        stack_level (int): How many levels down the stack the caller is
            from here. 1 indicates this function is being called from
            module scope, 2 indicates this function is being called from
            another function, etc.

    This will first get the package name of the module containing the
    caller. ``package_level`` segments will be then be chopped off of
    the package name.

    If this is called from a sub-package, ``package_level`` will have to
    be adjusted accordingly (add 1 for each sub-package).

    If this is called indirectly (e.g., via :func:`init_settings`)
    ``stack_level`` will have to be adjusted accordingly (add 1 for each
    nested function).

    """
    assert package_level >= 0, 'Package level should be greater than or equal to 0'
    assert stack_level > 0, 'Stack level should be greater than 0'
    frame = inspect.stack()[stack_level][0]
    package = frame.f_globals['__package__']
    package = package.rsplit('.', package_level)[0]
    return package


def get_module_globals(stack_level=2):
    frame = inspect.stack()[stack_level][0]
    return frame.f_globals
