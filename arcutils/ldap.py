from __future__ import absolute_import
import ldap
import ldap.filter
from django.conf import settings

# create a simple alias
escape = ldap.filter.escape_filter_chars

def ldapsearch(query):
    """Performs an ldapsearch and returns the results"""
    ld = ldap.initialize(settings.LDAP_URL)
    ld.simple_bind_s()
    results = ld.search_s(settings.LDAP_BASE_DN, ldap.SCOPE_SUBTREE, query)
    return results


def parse_profile(ldap_entry):
    f, l = parse_name(ldap_entry)
    return {
        "first_name": f,
        "last_name": l,
        "email": parse_email(ldap_entry),
        "odin": ldap_entry['uid'][0],
    }


def parse_name(ldap_entry):
    """
    Returns a two tuple: The user's first and last name derived from the ldapentry
    """
    if "sn" in ldap_entry:
        last_name = ldap_entry['sn'][0]
    else:
        last_name = ldap_entry.get("preferredcn", ldap_entry['cn'])[0].split(" ")[1:]

    first_name = ldap_entry.get("givenName", ldap_entry.get("preferredcn", ldap_entry['cn']))[0].split(" ")[0]

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
