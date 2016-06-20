from arcutils.settings import PrefixedSettings


DEFAULTS = {
    'default': {
        # Notes:
        #    - There are two LDAP hosts, ldap-bulk and ldap-login; Elliot has
        #      said that ldap-login "has more servers in the pool" and he
        #      recommends using it over ldap-bulk (RT ticket #580686); note that
        #      despite the name, ldap-login does not actually require auth
        #    - It's possible to do unauthenticated requests over SSL
        #    - It's also possible to do authenticated requests over non-SSL
        #    - To use SSL, set ``use_ssl`` to ``true``
        #    - A project will need an LDAP service account if it does LDAP
        #      requests that return more than 2,000 results
        #    - The defaults here support a typical Odin autocomplete scenario

        'host': 'ldap-login.oit.pdx.edu',
        'port': None,
        'use_ssl': False,
        'search_base': 'ou=people,dc=pdx,dc=edu',
        'username': None,
        'password': None,
        'strategy': 'SYNC',

        'tls': {
            'ca_certs_file': 'certifi:cacert.pem',
            'validate': 'CERT_REQUIRED',

            # This can be set to one of the protocol versions in the ssl module
            # (e.g., "PROTOCOL_SSLv23"); if it's not set, the ldap3 library will
            # choose a default value (which is "PROTOCOL_SSLv23" currently)
            'version': None,
        }
    },

    # Active Directory
    # To connect to AD, a service account is required; request it from
    # cis-windows.
    'ad': {
        'hosts': ['oitdcpsu01.psu.ds.pdx.edu', 'oitdcpsu02.psu.ds.pdx.edu'],
        'use_ssl': True,
        'strategy': 'SYNC',
        'search_base': 'ou=people,dc=psu,dc=ds,dc=pdx,dc=edu',
        # These are required for AD and must be in the project's local settings:
        # 'username': None,
        # 'password': None,
    }
}


class Settings(PrefixedSettings):

    def get(self, key, default=None, using='default'):
        using_key = '{using}.{key}'.format(using=using, key=key)
        return super().get(using_key, default)


settings = Settings('LDAP', DEFAULTS)
