import ldap3
from ldap3.utils.conv import escape_filter_chars as escape  # noqa

from arcutils.settings import get_setting


def get_ldap_settings(using='default'):
    """Get LDAP settings for the specified connection.

    Args:
        using: The name of an LDAP connection specified in the project's
            settings

    Returns:
        dict: Settings for connection

    """
    return get_setting('LDAP.{using}'.format(using=using))


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
