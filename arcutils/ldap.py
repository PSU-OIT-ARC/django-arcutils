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
    """
    From an LDAP entry, parse out the first name, last name, email address and
    ODIN username.

    Usage:
    results = ldapsearch("odin=mdj2")
    dn, entry = results[0]
    parse_profile(entry)
    """
    f, l = parse_name(ldap_entry)
    return {
        "first_name": f,
        "last_name": l,
        "email": parse_email(ldap_entry),
        "odin": ldap_entry['uid'][0],
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
