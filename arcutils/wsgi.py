import os
import site
import sys


def create_wsgi_application(settings_module, here, root=None, local_settings_file=None):
    """Create a WSGI application.

    This wraps Django's :func:`django.core.wsgi.get_wsgi_application` to
    do our standard boilerplate setup.

    To use this in an ARC project, replace the contents of its wsgi.py
    with this (replacing '{package}' with the project's actual top level
    package name)::

        from arcutils.wsgi import create_wsgi_application
        application = create_wsgi_application('{package}.settings', __file__)

    It's necessary to pass ``here`` so we can figure out where the root
    directory is. It's assumed that the root directory is always one
    directory up from wherever wsgi.py is located. Alternatively, you
    can pass a ``root`` directory explicitly.

    """
    if root is None:
        if os.path.isfile(here):
            here = os.path.dirname(here)
        root = os.path.dirname(here)

    if local_settings_file is None:
        local_settings_file = os.path.join(root, 'local.cfg')

    major, minor = sys.version_info[:2]
    site_packages = 'lib/python{major}.{minor}/site-packages'.format(**locals())
    site_packages = os.path.join(root, '.env', site_packages)

    if not os.path.isdir(site_packages):
        raise NotADirectoryError(
            'Could not find virtualenv site-packages at {}'.format(site_packages))

    # Add the virtualenv's site-packages to sys.path, ensuring its packages
    # take precedence over system packages (by moving them to the front of
    # sys.path after they're added).
    old_sys_path = list(sys.path)
    site.addsitedir(site_packages)
    new_sys_path = [item for item in sys.path if item not in old_sys_path]
    sys.path = new_sys_path + old_sys_path

    os.environ.setdefault('LOCAL_SETTINGS_FILE', local_settings_file)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    from django.core.wsgi import get_wsgi_application
    return get_wsgi_application()
