import importlib
import os.path


def abs_path(path, *rel_path):
    """Noramalize ``path`` to an absolute path.

    ``path`` may be a relative or absolute file system path or an asset
    path. If ``path`` is already an abs. path, it will be returned as
    is. Otherwise, it will be converted into a normalized abs. path.

    """
    if not os.path.isabs(path):
        if ':' in path:
            path = asset_path(path)
        else:
            path = os.path.expanduser(path)
            path = os.path.normpath(os.path.abspath(path))
    return path


def asset_path(path, *rel_path):
    """Compute absolute path to asset in package.

    ``path`` can be just a package name like 'arcutils' or it can be
    a package name and a relative file system path like
    'arcutils:some/path'.

    If ``rel_path`` is passed, it will be joined to the abs. path
    computed from ``path``.

    In the following examples, the '...' at the beginning of each path
    is the absolute path to wherever the django-arcutils package is
    installed.

        >>> asset_path('arcutils')
        '.../django-arcutils/arcutils'
        >>> asset_path('arcutils:local.base.cfg')
        '.../django-arcutils/arcutils/local.base.cfg'
        >>> asset_path('arcutils:templates/foundation.html')
        '.../django-arcutils/arcutils/templates/foundation.html'
        >>> asset_path('arcutils:templates', 'foundation.html')
        '.../django-arcutils/arcutils/templates/foundation.html'

    """
    if ':' in path:
        package_name, base_rel_path = path.split(':')
        rel_path = (base_rel_path,) + rel_path
    else:
        package_name = path
    package = importlib.import_module(package_name)
    if not hasattr(package, '__file__'):
        raise TypeError("Can't compute path relative to namespace package")
    package_path = os.path.dirname(package.__file__)
    path = os.path.join(package_path, *rel_path)
    path = os.path.normpath(os.path.abspath(path))
    return path
