"""Create a WSGI application.

This wraps Django's :func:`django.core.wsgi.get_wsgi_application` to do
our standard boilerplate setup.

To use this in an ARC project, *copy* the contents of this file into the
project's ``wsgi`` module (replacing whatever's already there) and add
the following at the bottom::

    application = create_wsgi_application('{package}.settings')

In most cases, the additional args to :func:`create_wsgi_application`
won't need to be passed.

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


def create_wsgi_application(settings_module=None, root=None, venv=None, local_settings_file=None,
                            daily_tasks_home=None):
    """Create a WSGI application.

    Configuration is done via environment variables. If any of the
    relevant environment variables (see below) aren't set, we fall back
    to defaults, which are either passed to this function explicitly or
    computed based on the location of the ``wsgi.py`` file.

    Environment variables:
        - WSGI_ROOT (root directory): This is used to locate the top
            level package directory, virtualenv, Django settings module,
            local settings file, etc when any of these aren't specified.
        - WSGI_VENV (virtualenv directory): The top level directory of
            the virtualenv the project is installed into. This is used
            to add the virtualenv's site packages to ``sys.path``.
        - DJANGO_SETTINGS_MODULE (django settings module): The Django
            settings module.
        - LOCAL_SETTINGS_FILE (local settings file): The Django local
            settings file.

    Args:
        root: The directory containing the directory containing the
            ``wsgi.py`` file. In a typical Django project, this is the
            top level project directory.
        venv: ``{root}/.env``
        settings_module: ``{root directory name}.settings``
        local_settings_file: ``{root}/local.cfg``
        daily_tasks_home: ``{root}``

    As an example, consider a project named ``pants`` with a top level
    package that is also named ``pants``. It's basic structure would be
    something like this::

        /home/user/projects/pants
            pants/
                settings.py
                wsgi.py
            local.cfg
            setup.py

    To create the WSGI application for this example project, all we have
    to do is call this function in global scope of the ``pants.wsgi``
    module::

        application = create_wsgi_application('pants.settings')

    In this case the environment variables will be set as follows::

        WSGI_ROOT = '/home/user/projects/pants'
        WSGI_VENV = '/home/user/projects/pants/.env'
        DJANGO_SETTINGS_MODULE = 'pants.settings'
        LOCAL_SETTINGS_FILE = '/home/user/projects/pants/local.cfg'

    """
    containing_dir = os.path.dirname(__file__)
    dir_name = os.path.basename(containing_dir)

    root = os.environ.setdefault('WSGI_ROOT', root or os.path.dirname(containing_dir))
    venv = os.environ.setdefault('WSGI_VENV', venv or os.path.join(root, '.env'))

    settings_module = settings_module or '{dir_name}.settings'.format(**locals())
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    local_settings_file = local_settings_file or os.path.join(root, 'local.cfg')
    os.environ.setdefault('LOCAL_SETTINGS_FILE', local_settings_file)

    daily_tasks_home = daily_tasks_home or root

    major, minor = sys.version_info[:2]
    site_packages_rel_path = 'lib/python{major}.{minor}/site-packages'.format(**locals())
    site_packages = os.path.join(venv, site_packages_rel_path)

    if not os.path.isdir(site_packages):
        message = 'Could not find virtualenv site-packages at {site_packages}'.format(**locals())
        raise NotADirectoryError(message)

    # Add the virtualenv's site-packages to sys.path, ensuring its packages
    # take precedence over system packages (by moving them to the front of
    # sys.path after they're added).
    old_sys_path = list(sys.path)
    site.addsitedir(site_packages)
    new_sys_path = [item for item in sys.path if item not in old_sys_path]
    sys.path = new_sys_path + old_sys_path

    from django.conf import settings
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application

    app = get_wsgi_application()

    if not settings.DEBUG:
        from arcutils.tasks import DailyTasksProcess
        daily_tasks = DailyTasksProcess(home=daily_tasks_home)
        daily_tasks.add_task(call_command, 3, 1, ('clearsessions',), name='clearsessions')
        daily_tasks.start()

    return app


# IMPORTANT: Pass the settings module for the project or ensure the
#            DJANGO_SETTINGS_MODULE environment variable is always set.
application = create_wsgi_application('SET THIS TO THE CORRECT VALUE FOR THIS PROJECT')
