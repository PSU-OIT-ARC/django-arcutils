"""
This module assumes you have a Django setting called LDAP that looks like:

settings.LDAP = {
    "default": {
        "host": "ldap://ldap-bulk.oit.pdx.edu",
        "username": "rethinkwebsite,ou=service,dc=pdx,dc=edu",
        "password": "foobar",
        "search_dn": "ou=people,dc=pdx,dc=edu",
        "ca_file": "/path/to/ca_file.crt",
    }
}
"""
import ssl

import ldap3

from django.conf import settings


def escape(s):
    """python3-ldap doesn't include this for some reason."""
    s = s.replace('\\', r'\\5C')
    s = s.replace('*', r'\\2A')
    s = s.replace('(', r'\\28')
    s = s.replace(')', r'\\29')
    s = s.replace('\0', r'\\00')
    return s


def connect(using="default"):
    """
    Connect to the LDAP server in the LDAP settings dict with the name `using`
    """
    config = settings.LDAP[using]

    if config.get('tls'):
        tls = ldap3.Tls(
            ca_certs_file=config.get('ca_file'),
            validate=ssl.CERT_REQUIRED,
        )
    else:
        tls = None

    if '_server' not in config:
        server = ldap3.Server(config['host'], tls=tls)
        config['_server'] = server

    conn = ldap3.Connection(
        config['_server'],
        auto_bind=True,
        user=config.get('username'),
        password=config.get('password'),
        lazy=True,
    )

    return conn


def ldapsearch(query, using="default", attributes=ldap3.ALL_ATTRIBUTES,
               **kwargs):
    """Performs an LDAP search and returns the results.

    If there are results, they will be returned as a list of 2-tuples.
    The first item in each tuple will be the ``dn``. The second item
    will be a dictionary containing the attributes specified via
    ``attributes`` (all attributes by default).

    If there are no results, and empty list will be returned.

    ``query`` should be well-formed LDAP query string, escaped if
    necessary. E.g.::

        '(uid=bob)'

    ``using`` specifies which LDAP settings to use from the ``LDAP``
    settings dict.

    ``attributes`` and all other keyword args are sent directly to
    :meth:`ldap3.Connection.search`.

    """
    connection = connect(using)
    config = settings.LDAP[using]
    with connection:
        result = connection.search(
            search_base=config['search_dn'],
            search_filter=query,
            search_scope=ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
            attributes=attributes,
            **kwargs)
    if result:
        return [(r['dn'], r['attributes']) for r in connection.response]
    return []


def parse_profile(ldap_entry):
    """Parse fields from LDAP entry into a dict.

    Items that will be present in the returned dict:

        - first_name
        - last_name
        - full_name (may include a middle initial)
        - title
        - ou (Organizational unit, unparsed)
        - school_or_office
        - department
        - email
        - odin (ODIN username)

    Usage::

        results = ldapsearch('odin=mdj2')
        dn, entry = results[0]
        parse_profile(entry)

    """
    first_name, last_name = parse_name(ldap_entry)
    full_name = ldap_entry.get('preferredcn', ldap_entry.get('cn', ['']))[0]
    full_name = full_name.split(',', 1)[0]
    title = ldap_entry.get('title', [''])[0]

    # XXX: This part is wonky. I'm not sure how many OU parts there can
    #      be or what there proper names are (school vs office, etc).
    ou = ldap_entry.get('ou')
    if ou and ou[0]:
        ou = ou[0]
        ou_parts = ou.split(' - ', 1)
        if len(ou_parts) == 1:
            school_or_office = ou_parts[0]
            department = None
        else:
            school_or_office = ou_parts[1]
            department = ou_parts[0]
    else:
        ou = None
        school_or_office = department = None

    return {
        'first_name': first_name,
        'last_name': last_name,
        'full_name': full_name,
        'title': title,
        'ou': ou,
        'school_or_office': school_or_office,
        'department': department,
        'email': parse_email(ldap_entry),
        'odin': ldap_entry['uid'][0],
    }


def parse_name(ldap_entry):
    """Return the user's first and last name as a 2-tuple.

    This is messy because there's apparently no canonical field to pull
    the user's first and last name from and also because the user's
    surname field (for example) may contain a title at the end (like
    "Bob Smith, Assistant Professor").

    """
    first_name = ldap_entry.get(
        'givenName', ldap_entry.get('preferredcn', ldap_entry.get('cn', [''])))
    first_name = first_name[0].split(' ')[0]
    if 'sn' in ldap_entry:
        last_name = ldap_entry['sn'][0].split(',', 1)[0]
    else:
        last_name = ldap_entry.get('preferredcn', ldap_entry.get('cn', ['']))
        last_name = last_name[0].split(',', 1)[0].split(' ')[-1]
    return first_name, last_name


def parse_email(ldap_entry):
    """
    Returns the user's email address from an ldapentry
    """
    if "mail" in ldap_entry:
        email = ldap_entry['mail'][0]
    else:
        email = ldap_entry['uid'][0] + "@pdx.edu"

    return email
