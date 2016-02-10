import ssl

from django.core.exceptions import ImproperlyConfigured

from ldap3 import Connection, Server, ServerPool, Tls

from arcutils.path import abs_path

from .utils import get_ldap_settings, setting_to_ldap3_attr


def connect(using='default') -> Connection:
    """Connect to the LDAP server indicated by ``using``.

    Args:
        using: The name of an LDAP connection specified in the project's
            settings

    Returns:
        Connection

    """
    config = get_ldap_settings(using)

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
        tls = Tls(ca_certs_file=ca_certs_file, validate=validate, version=version)
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
        server = Server(host, **server_args)
    else:
        hosts = [Server(h, **server_args) for h in hosts]
        server = ServerPool(hosts)

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

    return Connection(server, **client_args)
