import ldap3
from ldap3.utils.conv import escape_filter_chars as escape  # noqa


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
