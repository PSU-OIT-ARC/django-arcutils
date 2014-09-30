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
from __future__ import absolute_import
import tempfile
import ldap
import ldap.filter
from django.conf import settings

# create a simple alias
escape = ldap.filter.escape_filter_chars

def connect(using="default"):
    """
    Connect to the LDAP server in the LDAP settings dict with the name `using`
    """
    config = settings.LDAP[using]
    # we cache the connection so we don't have to reconnect every time we want
    # to use LDAP
    if '_conn' in config:
        return config['_conn']

    if config.get("ca_file"):
        ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, config['ca_file'])
    if config.get("ca_dir"):
        ldap.set_option(ldap.OPT_X_TLS_CACERTDIR, config['ca_dir'])

    conn = ldap.initialize(config['host'])
    conn.protocol_version = ldap.VERSION3
    if config.get("tls"):
        conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
        conn.start_tls_s()

    conn.simple_bind_s(config['username'], config['password'])
    # cache the connection so we don't reconnect
    config['_conn'] = conn
    return conn


def ldapsearch(query, using="default", **kwargs):
    """Performs an ldapsearch and returns the results"""
    connection = connect(using)
    results = connection.search_s(settings.LDAP[using]['search_dn'], ldap.SCOPE_SUBTREE, query, **kwargs)
    return results


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
