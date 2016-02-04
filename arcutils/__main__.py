import argparse

from ldap3.core.exceptions import LDAPInvalidFilterError

from arcutils.colorize import printer
from arcutils.ldap import ldapsearch
from arcutils.settings import init_settings

from django.conf import global_settings, settings


def main(argv=None):
    base_settings = {}
    init_settings(base_settings, quiet=True)
    settings.configure(global_settings, **base_settings)

    parser = argparse.ArgumentParser(description='ArcUtils Commands')
    subparsers = parser.add_subparsers()

    ldap_parser = subparsers.add_parser('ldap')
    ldap_parser.set_defaults(command=ldap)
    ldap_parser.add_argument('query')
    ldap_parser.add_argument('--search-base', default=None)
    ldap_parser.add_argument(
        '--attributes', default=None, help='LDAP attributes to fetch, separated by commas')
    ldap_parser.add_argument('--parse', default=True, action='store_true', dest='parse')
    ldap_parser.add_argument('--no-parse', default=True, action='store_false', dest='parse')
    ldap_parser.add_argument('--using', default='default')

    args = parser.parse_args(argv)
    if hasattr(args, 'command'):
        status = args.command(args)
        parser.exit(status or 0)
    else:
        parser.print_help()


def ldap(args):
    q = args.query
    using = args.using
    search_base = args.search_base
    attributes = args.attributes
    parse = args.parse

    if attributes is not None:
        attributes = [a.strip() for a in attributes.split(',')]

    try:
        results = ldapsearch(
            q, using=using, search_base=search_base, attributes=attributes, parse=parse)
    except LDAPInvalidFilterError:
        printer.error('Invalid LDAP filter: {q}'.format(q=q))
        printer.error('Is the query wrapped in parens?')
        return 1

    if not results:
        printer.error('No results found')
        return 2

    for r in results:
        if not parse:
            print('dn', '=>', r['dn'], '\n')
            r = r['attributes']
        for k in sorted(r.keys()):
            v = r[k]
            print(k, '=>', v)


if __name__ == '__main__':
    main()
