import ssl
from functools import partial

from django.core.exceptions import ImproperlyConfigured

import ldap3
from ldap3 import Connection, Server, ServerPool, Tls

from arcutils.path import abs_path

from .settings import settings
from .utils import setting_to_ldap3_attr


def connect(using='default') -> Connection:
    """Connect to the LDAP server indicated by ``using``.

    Args:
        using: The name of an LDAP connection specified in the project's
            settings

    Returns:
        Connection

    """
    get = partial(settings.get, using=using)

    host = get('host', None)
    hosts = get('hosts', None)

    if host and hosts:
        raise ImproperlyConfigured('LDAP: You can only specify one of `host` or `hosts`')
    if not (host or hosts):
        raise ImproperlyConfigured('LDAP: You must specify one of `host` or `hosts`')

    use_ssl = get('use_ssl', False)
    tls_config = get('tls', {})

    if use_ssl and tls_config:
        ca_certs_file = tls_config.get('ca_certs_file')
        if ca_certs_file:
            ca_certs_file = abs_path(ca_certs_file)
        validate = tls_config.get('validate', 'CERT_REQUIRED')
        validate = getattr(ssl, validate)
        version = tls_config.get('version')
        if version:
            version = getattr(ssl, version)
        tls = Tls(ca_certs_file=ca_certs_file, validate=validate, version=version)
    else:
        # If use_ssl is True but no TLS settings are specified, the
        # ldap3 library will use a default TLS configuration, which is
        # probably not what you want.
        tls = None

    server_args = {
        'port': get('port', None),
        'use_ssl': use_ssl,
        'tls': tls,
        'get_info': ldap3.NONE,
    }

    if host:
        server = Server(host, **server_args)
    else:
        hosts = [Server(h, **server_args) for h in hosts]
        server = ServerPool(hosts)

    client_args = {
        'user': get('username', None),
        'password': get('password', None),
        'auto_bind': setting_to_ldap3_attr(get('auto_bind', 'AUTO_BIND_NONE')),
        'authentication': setting_to_ldap3_attr(get('authentication', None)),
        'client_strategy': setting_to_ldap3_attr(get('strategy', 'SYNC')),
        'read_only': get('read_only', True),
        'lazy': get('lazy', True),
        'raise_exceptions': get('raise_exceptions', True),
        'pool_name': get('pool_name', None),
        'pool_size': get('pool_size', None),
        'pool_lifetime': get('pool_lifetime', None),
    }

    return Connection(server, **client_args)
