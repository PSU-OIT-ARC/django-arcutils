"""LDAP functionality.

This module assumes that a project has at least these minimal LDAP
settings::

    LDAP = {
        'default': {
            'host': 'ldap://ldap-bulk.oit.pdx.edu',
            'search_base': 'ou=people,dc=pdx,dc=edu',
        }
    }

Depending on the project, a username and password or other settings may
also be requred. There's a bit of documentation on this in the base
local settings file (local.base.cfg).

TODO: Incorporate the ldap3 library's abstraction layer:
      http://ldap3.readthedocs.org./abstraction.html

"""
import functools
import re
import ssl
from collections import defaultdict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import ldap3
from ldap3.utils.dn import parse_dn as _parse_dn

from .path import abs_path
from .registry import get_registry


def escape(s):
    """ldap3 doesn't include this for some reason."""
    s = s.replace('\\', r'\\5C')
    s = s.replace('*', r'\\2A')
    s = s.replace('(', r'\\28')
    s = s.replace(')', r'\\29')
    s = s.replace('\0', r'\\00')
    return s


def setting_to_ldap3_attr(v):
    if isinstance(v, str):
        return getattr(ldap3, v)
    return v


def connect(using='default'):
    """Connect to the LDAP server indicated by ``using``."""
    config = settings.LDAP[using]

    host = config.get('host')
    hosts = config.get('hosts')

    if host and hosts:
        raise ImproperlyConfigured('LDAP: You can only specify one of `host` or `hosts`')
    if not (host or hosts):
        raise ImproperlyConfigured('LDAP: You must specify one of `host` or `hosts`')

    use_ssl = config.get('use_ssl', False)
    tls_config = config.get('tls')

    if use_ssl and tls_config:
        ca_certs_file = tls_config.get('ca_certs_file')
        if ca_certs_file:
            ca_certs_file = abs_path(ca_certs_file)
        validate = tls_config.get('validate', 'CERT_REQUIRED')
        validate = getattr(ssl, validate)
        version = tls_config.get('version')
        if version:
            version = getattr(ssl, version)
        tls = ldap3.Tls(ca_certs_file=ca_certs_file, validate=validate, version=version)
    else:
        # If use_ssl is True but no TLS settings are specified, the
        # ldap3 library will use a default TLS configuration, which is
        # probably not what you want.
        tls = None

    server_args = {
        'port': config.get('port'),
        'use_ssl': use_ssl,
        'tls': tls,
    }

    if host:
        server = ldap3.Server(host, **server_args)
    else:
        hosts = [ldap3.Server(h, **server_args) for h in hosts]
        server = ldap3.ServerPool(hosts)

    client_args = {
        'user': config.get('username'),
        'password': config.get('password'),
        'auto_bind': setting_to_ldap3_attr(config.get('auto_bind', 'AUTO_BIND_NONE')),
        'authentication': setting_to_ldap3_attr(config.get('authentication')),
        'client_strategy': setting_to_ldap3_attr(config.get('strategy', 'SYNC')),
        'read_only': config.get('read_only', True),
        'lazy': config.get('lazy', True),
        'raise_exceptions': config.get('raise_exceptions', True),
        'pool_name': config.get('pool_name'),
        'pool_size': config.get('pool_size'),
        'pool_lifetime': config.get('pool_lifetime'),
    }

    return ldap3.Connection(server, **client_args)


def ldapsearch(query, connection=None, using='default', search_base=None, attributes=None,
               parse=True, **kwargs):
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
    config = settings.LDAP[using]
    search_base = search_base or config['search_base']
    attributes = attributes or config.get('attributes') or ldap3.ALL_ATTRIBUTES

    if connection is None:
        registry = get_registry()
        connection = registry.get_component(ldap3.Connection, name=using)
        if connection is None:
            connection = connect(using)

    with connection:
        result = connection.search(
            search_base=search_base,
            search_filter=query,
            search_scope=ldap3.SEARCH_SCOPE_WHOLE_SUBTREE,
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
        - email_address (preferred address)
        - canonical_email_address (from mailRoutingAddress)
        - email_addresses (all addresses, in this order: preferred, canonical, aliases)
        - username (ODIN username)
        - phone number
        - phone extension
        - room number
        - roles
        - password_expiration_date
        - member_of (AD groups; only populated when querying AD)

    Usage::

        >>> results = ldapsearch('(uid=mdj2)', parse=False)
        >>> attributes = results[0]['attributes']
        >>> parse_profile(attributes)
        {'first_name': 'Matthew', 'last_name': 'Johnson', 'username': 'mdj2', ...}

    """
    get = functools.partial(_get_attribute, attributes)

    first_name, last_name = parse_name(attributes)
    full_name = get('preferredcn') or get('displayName') or get('cn') or ''
    full_name = full_name.split(',', 1)[0]
    title = get('title')

    # XXX: This part is wonky. I'm not sure how many OU parts there can
    #      be or what there proper names are (school vs office, etc).
    ou = get('ou') or get('department')
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

    username = get('uid') or get('name')

    preferred_email_address = parse_email(attributes)
    canonical_email_address = get('mailRoutingAddress') or get('mail')
    email_addresses = [preferred_email_address] if preferred_email_address else []
    additional_email_addresses = get('mailRoutingAddress', True) + get('mailLocalAddress', True)
    for a in additional_email_addresses:
        if a not in email_addresses:
            email_addresses.append(a)

    phone_number = parse_phone_number(attributes)
    extension = parse_psu_extension(attributes, phone_number)

    return {
        'first_name': first_name,
        'last_name': last_name,
        'full_name': full_name,
        'title': title,
        'ou': ou,
        'school_or_office': school_or_office,
        'department': department,
        'email_address': preferred_email_address,
        'email_addresses': email_addresses,
        'canonical_email_address': canonical_email_address,
        'odin': username,  # deprecated
        'username': username,
        'phone_number': phone_number,
        'extension': extension,
        'room_number': get('roomNumber') or get('physicalDeliveryOfficeName'),
        'roles': get('eduPersonAffiliation', True),
        'password_expiration_date': _reformat_datetime(get('psuPasswordExpireDate')),
        'member_of': parse_member_of(attributes)
    }


def parse_name(attributes):
    """Return the user's first and last name as a 2-tuple.

    This is messy because there's apparently no canonical field to pull
    the user's first and last name from and also because the user's
    surname field (for example) may contain a title at the end (like
    "Bob Smith, Assistant Professor").

    """
    get = functools.partial(_get_attribute, attributes)

    # We try to extract the first and/or last name from this if
    # necessary.
    fallback = get('preferredcn') or get('displayName') or get('cn') or ''

    first_name = get('givenName')
    if not first_name:
        first_name = fallback.split(' ')[0]

    surname = get('sn')
    if surname:
        last_name = surname.split(',', 1)[0]
    else:
        last_name = fallback.split(',', 1)[0].split(' ')[-1]

    return first_name, last_name


def parse_email(attributes, field='mail'):
    """Get preferred email address from LDAP attributes.

    By default, this pulls the address from the ``mail`` field, which
    (I think) is the user's preferred email address.

    Other options for ``field`` are "mailRoutingAddress" (canonical) and
    "mailLocalAddress" (aliases).

    """
    get = functools.partial(_get_attribute, attributes)
    allowed_fields = ('mail', 'mailLocalAddress', 'mailRoutingAddress')
    if field not in allowed_fields:
        raise ValueError(
            'Unknown email address field: "{field}"; must be one of: {allowed_fields}'
            .format_map(locals()))
    email = get(field)
    if not email:
        username = get('uid') or get('name')
        if username:
            email = '{uid}@pdx.edu'.format(uid=_get_attribute(attributes, 'uid'))
    return email


def parse_phone_number(attributes, phone_number=None):
    """Get phone number from LDAP attributes and standardize it.

    Tries to normalize a phone number to XXX-XXX-XXXX format. Does not
    normalize numbers with country codes, non-US formats, or any
    nonstandard characters. Also does not handle the case where a user
    has entered two phone numbers into the same field.

    Input formats that are handled after normalizing to remove
    whitespace, parentheses, dashes, and dots:

    - 10 digit number
    - 11 digit number starting with 1
    - 4 digit number (assumed to be a PSU extension)
      - Same but prefixed with an "x"
    - 5 digit number starting with 5 (assumed to be a PSU extension)
      - Same but prefixed with an "x"
    - Any of the above prefixed with "h." (indicating a home number,
      presumably)

    Args:
        attributes: If ``phone_number`` isn't specified, it will be
            retrieved from these LDAP attributes
        phone_number: A phone number

    Returns:
        str: A phone number formatted as AAA-PPP-NNNN if possible
        str: The original value from the telephoneNumber field if it
            can't be normalized to a 10-digit US number
        None: The telephoneNumber field is empty or contains a blank
            value after stripping whitespace

    .. note:: You *cannot* rely on the return value of this function
              being a normalized 10-digit US phone number.

    """
    if phone_number is None:
        phone_number = _get_attribute(attributes, 'telephoneNumber')

    if phone_number is None:
        return None

    phone_number = phone_number.strip()

    if not phone_number:
        return None

    if re.search(r'^[2-9]\d{2}-\d{3}-\d{4}$', phone_number):
        # Short circuit if already normalized
        return phone_number

    original_value = phone_number

    # "h." prefix indicates a home number? Maybe?
    if phone_number.startswith('h.'):
        phone_number = phone_number[2:]
        phone_number = phone_number.strip()

    phone_number = re.sub('[\s()-.]', '', phone_number)

    # Add area code
    if re.search(r'^\d{7}$', phone_number):
        phone_number = '503{phone_number}'.format_map(locals())
    # Convert extension to full number
    elif re.search(r'^x?5\d{4}$', phone_number):
        extension = phone_number[1:] if phone_number.startswith('x') else phone_number
        phone_number = '50372{extension}'.format_map(locals())
    # Apparently, extensions are sometimes specified using just the last
    # four digits
    elif re.search(r'^x?\d{4}$', phone_number):
        extension = phone_number[1:] if phone_number.startswith('x') else phone_number
        phone_number = '503725{extension}'.format_map(locals())
    # Strip leading 1
    elif re.search(r'^1\d{10}$', phone_number):
        phone_number = phone_number[1:]

    # Normalize number by adding dashes between parts
    if re.search(r'^[2-9]\d{9}$', phone_number):
        phone_number = '-'.join((phone_number[:3], phone_number[3:6], phone_number[6:]))
    else:
        phone_number = original_value

    return phone_number


def parse_psu_extension(attributes, phone_number=None):
    """If phone number looks like a PSU number, return the extension.

    Args:
        attributes: If ``phone_number`` isn't specified, it will be
            retrieved from these LDAP attributes
        phone_number: A phone number

    The phone number, regardless of source, is normalized via
    :func:`parse_phone_number` first.

    Returns:
        str: The P-NNNN extension if the phone number looks like a PSU
            number
        None: The phone doesn't look like a PSU number

    """
    phone_number = parse_phone_number(attributes, phone_number)
    if phone_number and re.search(r'503-725-\d{4}$', phone_number):
        return phone_number[-6:]
    return None


def parse_member_of(attributes):
    """Parse AD ``memberOf`` field into a list of dicts.

    The ``memberOf`` field contains items with this format::

        CN=AAA,OU=BBB,DC=PSU,DC=DS,DC=PDX,DC=EDU
        CN=XXX,OU=YYY,DC=PSU,DC=DS,DC=PDX,DC=EDU

    And this function will return a list of dicts like this::

        [{'name': 'AAA'}, {'name': 'BBB'}]

    """
    member_of = _get_attribute(attributes, 'memberOf', True)
    member_of = [parse_dn(m) for m in member_of]
    member_of = [{'name': dn['cn'][0]} for dn in member_of]
    return member_of


def parse_dn(string):
    """Parse a DN into a dict.

    For example::

        >>> parse_dn('CN=ABC,OU=XYZ,DC=PSU,DC=DS,DC=PDX,DC=EDU')
        {'cn': ['ABC'], 'dc': ['PSU', 'DS', 'PDX', 'EDU'], 'ou': ['XYZ']}

    Note that the keys get lower-cased for consistent access, but the
    values are left as is.

    """
    dn = defaultdict(list)
    for parts in _parse_dn(string):
        k, v, *rest = parts
        dn[k.lower()].append(v)
    return dict(dn)


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

    If the attribute doesn't exist, ``None`` will be returned if
    ``all=False`` and ``[]`` will be returned if ``all=True``.

    If the attribute does exist, its first value will be returned by
    default. If ``all=True``, the complete list of values will be
    returned.

    .. note:: All LDAP attribute values are lists, even where this
              doesn't make logical sense.

    All values in the attribute's list will be stripped of leading and
    trailing whitespace. Any values that are empty strings will then be
    discarded. If the list is empty after this, ``None`` will be
    returned if ``all=False``.

    .. note:: A list is always returned when ``all`` is set.

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
        attr = [] if all else None
    return attr
