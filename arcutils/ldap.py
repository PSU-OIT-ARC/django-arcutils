"""LDAP functionality.

This module assumes an LDAP setting like so::

    LDAP = {
        'default': {
            'host': 'ldap://ldap-bulk.oit.pdx.edu',
            'username': 'rethinkwebsite,ou=service,dc=pdx,dc=edu',
            'password': 'foobar',
            'search_base': 'ou=people,dc=pdx,dc=edu',
            'ca_file': '/path/to/ca_file.crt',
        }
    }

"""
import functools
import re
import ssl

from django.conf import settings

import ldap3


def escape(s):
    """ldap3 doesn't include this for some reason."""
    s = s.replace('\\', r'\\5C')
    s = s.replace('*', r'\\2A')
    s = s.replace('(', r'\\28')
    s = s.replace(')', r'\\29')
    s = s.replace('\0', r'\\00')
    return s


def connect(using='default'):
    """Connect to the LDAP server indicated by ``using``."""
    config = settings.LDAP[using]
    if config.get('tls'):
        tls = ldap3.Tls(ca_certs_file=config.get('ca_file'), validate=ssl.CERT_REQUIRED)
    else:
        tls = None
    server = ldap3.Server(config['host'], use_ssl=True, tls=tls)
    username = config.get('username')
    password = config.get('password')
    return ldap3.Connection(server, auto_bind=True, user=username, password=password, lazy=True)


def ldapsearch(query, using='default', search_base=None, parse=True,
               attributes=ldap3.ALL_ATTRIBUTES, **kwargs):
    """Performs an LDAP search and returns the results.

    If there are results, they will be parsed via :func:`parse_profile`
    unless ``parse=False``.

    If there are no results, an empty list will be returned.

    ``query`` should be well-formed LDAP query string, escaped if
    necessary. E.g.::

        '(uid=bob)'

    ``using`` specifies which LDAP settings to use from the ``LDAP``
    settings dict.

    ``attributes`` and all other keyword args are sent directly to
    :meth:`ldap3.Connection.search`.

    """
    # XXX: This creates a new connection for every search; should we be
    #      using a connection pool?
    connection = connect(using)
    if search_base is None:
        config = settings.LDAP[using]
        search_base = config['search_base']
    with connection:
        result = connection.search(
            search_base=search_base,
            search_filter=query,
            search_scope=ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
            attributes=attributes,
            **kwargs)
    if not result:
        return []
    if parse:
        return [parse_profile(r['attributes']) for r in connection.response]
    return connection.response


def parse_profile(attributes):
    """Parse fields from LDAP attributes into a dict.

    Items that will be present in the returned dict:

        - first_name
        - last_name
        - full_name (may include a middle initial)
        - title
        - ou (Organizational unit, unparsed)
        - school_or_office
        - department
        - email_address (primary address)
        - email_addresses (all addresses)
        - odin (ODIN username)
        - phone number
        - phone extension
        - room number
        - roles
        - password_expiration_date

    Usage::

        >>> results = ldapsearch('(uid=mdj2)', parse=False)
        >>> attributes = results[0]['attributes']
        >>> parse_profile(attributes)
        {'first_name': 'Matthew', 'last_name': 'Johnson', 'odin': 'mdj2', ...}

    """
    get = functools.partial(_get_attribute, attributes)

    first_name, last_name = parse_name(attributes)
    full_name = get('preferredcn') or get('cn') or ''
    full_name = full_name.split(',', 1)[0]
    title = get('title')

    # XXX: This part is wonky. I'm not sure how many OU parts there can
    #      be or what there proper names are (school vs office, etc).
    ou = get('ou')
    if ou:
        ou_parts = ou.split(' - ', 1)
        if len(ou_parts) == 1:
            school_or_office = ou_parts[0]
            department = None
        else:
            school_or_office = ou_parts[1]
            department = ou_parts[0]
    else:
        ou = school_or_office = department = None

    odin = get('uid')
    email_address = parse_email(attributes)
    phone_number = parse_phone_number(attributes)
    extension = phone_number[-6:] if phone_number else None

    return {
        'first_name': first_name,
        'last_name': last_name,
        'full_name': full_name,
        'title': title,
        'ou': ou,
        'school_or_office': school_or_office,
        'department': department,
        'email_address': email_address,
        'email_addresses': get('mailLocalAddress', True),
        'odin': odin,
        'phone_number': phone_number,
        'extension': extension,
        'room_number': get('roomNumber'),
        'roles': get('eduPersonAffiliation', True),
        'password_expiration_date': _reformat_datetime(get('psuPasswordExpireDate')),
    }


def parse_name(attributes):
    """Return the user's first and last name as a 2-tuple.

    This is messy because there's apparently no canonical field to pull
    the user's first and last name from and also because the user's
    surname field (for example) may contain a title at the end (like
    "Bob Smith, Assistant Professor").

    """
    get = functools.partial(_get_attribute, attributes)
    first_name = get('givenName') or get('preferredcn') or get('cn') or ''
    first_name = first_name.split(' ')[0]
    surname = get('sn')
    if surname:
        last_name = surname.split(',', 1)[0]
    else:
        last_name = get('preferredcn') or get('cn') or ''
        last_name = last_name.split(',', 1)[0].split(' ')[-1]
    return first_name, last_name


def parse_email(attributes):
    """Get email address from LDAP attributes."""
    email = _get_attribute(attributes, 'mail')
    if not email:
        email = '{uid}@pdx.edu'.format(uid=_get_attribute(attributes, 'uid'))
    return email


def parse_phone_number(attributes):
    """Get phone number from LDAP attributes and standardize it.

    Try to convert to XXX-XXX-XXXX format.

    .. note:: Does not deal with country codes, non-US formats, or any
              nonstandard characters.

    """
    phone_number = _get_attribute(attributes, 'telephoneNumber')
    if phone_number:
        phone_number = phone_number.strip()
        phone_number = phone_number.replace(' ', '-')
        phone_number = phone_number.replace('(', '')
        phone_number = phone_number.replace(')', '-')
        while '  ' in phone_number:
            phone_number = phone_number.replace('  ', ' ')
        while '--' in phone_number:
            phone_number = phone_number.replace('--', '-')
    return phone_number


def _reformat_datetime(dt):
    # Convert yyyyMMddHHmmssZ to ISO format yyyyMMddTHHmmssZ (put T
    # between date and time).
    if not dt:
        return
    if not re.search('^\d{14}Z$', dt):
        raise ValueError('Expected string with format yyyyMMddHHmmssZ; got {}'.format(dt))
    return '{}T{}'.format(dt[:8], dt[8:])


def _get_attribute(attributes, key, all=False):
    """Safely get the LDAP attribute specified by ``key``.

    If the attribute doesn't exist, ``None`` will be returned.

    If the attribute does exist, its first value will be returned by
    default. If ``all=True``, the complete list of values will be
    returned.

    .. note:: All LDAP attribute values are lists, even where this
              doesn't make logical sense.

    All values in the attribute's list will be stripped of leading and
    trailing whitespace. Any values that are empty strings will then be
    discarded. If the list is empty after this, ``None`` will be
    returned if ``all=False``.

    """
    if key in attributes:
        attr = attributes[key]
        attr = [v.strip() for v in attr]
        attr = [v for v in attr if v]
        if not all:
            try:
                attr = attr[0]
            except IndexError:
                attr = None
    else:
        attr = None
    return attr
