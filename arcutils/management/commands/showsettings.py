import sys
from collections import Mapping, Sequence
from fnmatch import fnmatch

from django.conf import settings
from django.core.management.base import BaseCommand

from arcutils.colorize import printer
from arcutils.settings import get_setting, get_settings_dict


class Command(BaseCommand):

    help = (
        'Show the value of one or more Django settings, nicely formatted. '
        'All settings will be shown by default, alphabetized.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'names', nargs='*', default=[],
            help='Settings can be specified using dotted names. '
                 'Examples: TEMPLATES, TEMPLATES.0, TEMPLATES.0.OPTIONS.'
        )
        parser.add_argument(
            '-d', '--depth', type=int, default=None,
            help='How deep to descend into settings. '
                 'By default, all settings are shown. '
                 'E.g., to show just top level settings, use `--depth 1`.'
        )
        parser.add_argument(
            '-e', '--exclude', nargs='*', default=[],
            help='List of dotted settings names to exclude. '
                 'Names can be shell-style patterns (*, ?, etc).')

    def handle(self, *args, **options):
        names = self.get_setting_names(options)
        depth = options['depth']
        exclude = set(options['exclude'])
        for name in names:
            try:
                value = get_setting(name)
            except KeyError:
                printer.error('Setting "{0}" not found'.format(name), file=sys.stderr)
            else:
                self.print(name, value, depth, exclude)

    def get_setting_names(self, options):
        names = options['names']
        if not names:
            return self.get_top_level_setting_names()
        return names

    def get_top_level_setting_names(self):
        names = sorted(get_settings_dict(settings))
        names = [n for n in names if not n.startswith('_')]
        return names

    def print(self, name, value, depth, exclude, parent_name=None, level=0):
        if level == depth:
            return

        full_name = name if parent_name is None else '.'.join((parent_name, str(name)))

        for pattern in exclude:
            if fnmatch(full_name, pattern):
                return

        indent = ' ' * (level * 4)

        parent_name = full_name
        level += 1

        print('{indent}{name} => '.format_map(locals()), end='')

        if isinstance(value, Mapping):
            if not value:
                print(repr(value))
            else:
                print()
                for k in sorted(value):
                    v = value[k]
                    self.print(k, v, depth, exclude, parent_name, level)
        elif isinstance(value, Sequence) and not isinstance(value, (bytes, str)):
            if not value:
                print(repr(value))
            else:
                print()
                for i, v in enumerate(value):
                    self.print(i, v, depth, exclude, parent_name, level)
        else:
            print(repr(value))
