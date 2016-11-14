import ldap3
from functools import partial

from ..registry import get_registry
from .connection import connect
from .profile import parse_profile
from .settings import settings


def ldapsearch(query, connection=None, using='default', search_base=None,
               search_scope=ldap3.SUBTREE, attributes=None, parse=True, **kwargs):
    """Performs an LDAP search and returns the results.

    If there are results, they will be parsed via :func:`parse_profile`
    unless ``parse=False``.

    If there are no results, an empty list will be returned.

    ``query`` should be well-formed LDAP query string, escaped if
    necessary. E.g.::

        '(uid=bob)'

    An LDAP ``connection`` object can be passed, and it will be used as
    is.

    If a ``connection`` isn't passed, we first look for one in the
    component registry (registered under ``ldap3.Connection``). If
    a connection object isn't found in the registry, one will be
    constructed from the ``LDAP`` settings indicated by ``using``.

    ``attributes`` and all other keyword args are sent directly to
    :meth:`ldap3.Connection.search`.

    """
    get = partial(settings.get, using=using)

    search_base = search_base or get('search_base')
    attributes = attributes or get('attributes', None) or ldap3.ALL_ATTRIBUTES

    if connection is None:
        registry = get_registry()
        connection = registry.get_component(ldap3.Connection, name=using)
        if connection is None:
            connection = connect(using)

    with connection:
        result = connection.search(
            search_base=search_base,
            search_filter=query,
            search_scope=search_scope,
            attributes=attributes,
            **kwargs)

        if connection.strategy.sync:
            # For synchronous strategies, result will be True or False.
            response = connection.response if result else []
        else:
            # For asynchronous strategies, result will be an int.
            response, _ = connection.get_response(result)

    return [parse_profile(r['attributes']) for r in response] if parse else response


def ldapsearch_by_email(email, **kwargs):
    """Perform LDAP search by ``email``.

    This looks for the ``email`` address in various LDAP fields.

    """
    # This odd formatting allows filters to be easily added or removed
    query = (
        '(|'
        '(mail={email})'
        '(mailLocalAddress={email})'
        '(mailRoutingAddress={email})'
        ')'
        .format(email=email)
    )
    return ldapsearch(query, **kwargs)
