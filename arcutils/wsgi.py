"""Create a WSGI application.

This wraps Django's :func:`django.core.wsgi.get_wsgi_application` to do
our standard boilerplate setup.

To use this in an ARC project, *copy* the contents of this file into the
project's ``wsgi`` module (replacing whatever's already there) and add
the following at the bottom::

    root = os.path.dirname(os.path.dirname(__file__))
    settings_module = '{package}.settings'
    application = create_wsgi_application(root, settings_module)

.. note:: These lines must be in the global scope. Also, make sure to
          set ``{package}`` to the project's top level package name.

.. note:: We can't import :func:`.create_wsgi_application` into the
          project's ``wsgi`` module in production because ``arcutils``
          isn't on ``sys.path`` until *after* `create_wsgi_application`
          is called (i.e., it's a bootstrapping issue).

"""
import os
import site
import sys


def create_wsgi_application(root, settings_module=None, local_settings_file=None):
    """Create a WSGI application anchored at ``root``.

    ``root`` must contain a virtualenv at ``./.env``.

    ``settings_module`` is only used if the ``DJANGO_SETTINGS_MODULE``
    environment variable is not already set.

    Likewise, ``local_settings_file`` is only used if the environment
    variable ``LOCAL_SETTINGS_FILE`` is not already set. The default
    value for this is ``{root}/local.cfg``. If a project doesn't use
    ``django-local-settings``, this will have no effect.

    """
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

    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.core.management import call_command

    if not settings.DEBUG:
        from arcutils.tasks import DailyTasksProcess
        daily_tasks = DailyTasksProcess(home=root)
        daily_tasks.add_task(call_command, 3, 1, ('clearsessions',), name='clearsessions')
        daily_tasks.start()

    return get_wsgi_application()


root = os.path.dirname(os.path.dirname(__file__))
settings_module = '{package}.settings'  # IMPORTANT: Replace {package}
application = create_wsgi_application(root, settings_module)
