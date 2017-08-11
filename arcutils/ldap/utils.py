from collections import defaultdict

import ldap3
from ldap3.utils.conv import escape_filter_chars as escape  # noqa
from ldap3.utils.dn import parse_dn as ldap3_parse_dn


def setting_to_ldap3_attr(name):
    """Get named attribute from ldap3 pacakge.

    Args:
        name (str): ldap3 attribute name

    Returns:
        object: The named ldap3 attribute if ``name`` is a string; if
            ``name`` is not a string, it's returned as is

    """
    if isinstance(name, str):
        return getattr(ldap3, name)
    return name


def parse_dn(dn):
    """Parse ``dn`` into parts.

    All parts of the same type are accumulated into lists. The typical
    types are `cn`, `ou`, and `dc`. Keys are lower-cased for consistent
    access, but the values are left as is.

    Special keys will be added when appropriate:

    - ``first_cn`` when ``cn`` is present
    - ``organization`` when ``o`` is present
    - ``top_level_ou`` when ``ou`` is present

        {
            cn: ['name'],
            o: ['PSU'],
            ou: ['OU1', 'OU2'],
            dc: ['example', 'com'],
            first_cn: 'name',
            organization: 'PSU',
            top_level_ou: 'OU1',
        }

    Example::

        >>> result = parse_dn('CN=NAME,OU=ACME,DC=EXAMPLE,DC=COM')
        >>> result['cn']
        ['NAME']
        >>> result['ou']
        ['ACME']
        >>> result['dc']
        ['EXAMPLE', 'COM']
        >>> result['first_cn']
        'NAME'
        >>> result['top_level_ou']
        'ACME'

    """
    result = defaultdict(list)
    parts = ldap3_parse_dn(dn)
    for part in parts:
        type_, value, _ = part
        type_ = type_.lower()
        items = result[type_]
        items.append(value)
    if 'cn' in result:
        result['first_cn'] = result['cn'][0]
    if 'o' in result:
        result['organization'] = result['o'][0]
    if 'ou' in result:
        result['top_level_ou'] = result['ou'][0]
    return result
