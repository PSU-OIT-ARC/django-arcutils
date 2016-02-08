"""LDAP functionality geared toward ARC projects.

This functionality is built on top of the ldap3 library:

- Docs: http://ldap3.readthedocs.org/
- GitHub: https://github.com/cannatag/ldap3
- PyPI: https://pypi.python.org/pypi/ldap3

This package assumes that a project has at least these minimal LDAP
settings::

    LDAP = {
        'default': {
            'host': 'ldap://ldap-bulk.oit.pdx.edu',
            'search_base': 'ou=people,dc=pdx,dc=edu',
        }
    }

Depending on the project, a username and password or other settings may
also be required. There's a bit of documentation on this in the base
local settings file (local.base.cfg).

TODO: Incorporate the ldap3 library's abstraction layer:
      http://ldap3.readthedocs.org./abstraction.html

"""
import ldap3

from .connection import connect
from .search import ldapsearch, ldapsearch_by_email
from .utils import escape  # noqa

CONNECTION_TYPE = ldap3.Connection
