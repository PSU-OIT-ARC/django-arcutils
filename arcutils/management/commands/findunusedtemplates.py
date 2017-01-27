import fnmatch
import mimetypes
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from arcutils.colorize import printer


class Command(BaseCommand):

    help = (
        'Check for unused templates. '
        'This can only provide a HINT at templates that MIGHT be unused.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'where', nargs='*', default=['.'],
            help='Where to look for usage of templates. '
                 'Multiple directories can be specified. '
                 'Defaults to the current directory.'
        )
        parser.add_argument(
            '-s', '--source', default='.',
            help='Where to find templates to check for usage. '
                 'Defaults to the current directory.'
        )
        parser.add_argument(
            '-e', '--exclude', nargs='*',
            default=[
                'search',
            ],
            help='Template subdirectories to exclude. '
                 'Multiple subdirectories can be specified. '
                 'Usually, these will correspond to app names.'
        )
        parser.add_argument(
            '--ignore-dirs', nargs='*',
            default=[
                '.*',
                '*.dist-info',
                '*.egg-info',
                '__pycache__',
                'build',
                'dist',
                'node_modules',
                'pip',
                'static',
                'venv',
            ],
            help='Do not look for templates or check for their usage in these directories.'
        )
        parser.add_argument(
            '--ignore-files', nargs='*',
            default=[
                '.*',
                'CHANGELOG*',
                'README*',
                '*.mo',
                '*.po',
                '*.so',
            ],
            help='Skip these files when checking for template usage.'
        )
        parser.add_argument('-d', '--debug', action='store_true', default=False)

    def handle(self, *args, **options):
        self.debug = options['debug']
        self.source = os.path.normpath(os.path.abspath(options['source']))
        self.where = [os.path.normpath(os.path.abspath(w)) for w in options['where']]
        self.exclude = options['exclude']
        self.ignore_dirs = options['ignore_dirs']
        self.ignore_files = options['ignore_files']
        self.all_files = self.get_files_to_check(self.where)

        source_dirs = self.get_source_dirs(self.source)
        source_files = self.get_source_files(source_dirs)
        unused = self.find_unused(source_files)
        num_unused = len(unused)

        if unused:
            s = '' if num_unused == 1 else 's'
            printer.warning('Found', num_unused, 'template{s} that MAY be unused:'.format(s=s))
            for entry in unused:
                full_path, short_path, base_name = entry
                print(os.path.relpath(full_path, self.source))
            printer.warning('NOTE: You CANNOT simply remove the templates listed above.')
            printer.warning('NOTE: You MUST check manually to ensure they are actually unused.')
        else:
            printer.success('No unused templates found')

    def find_unused(self, paths):
        unused = []
        for entry in paths:
            full_path, short_path, base_name = entry
            if self.debug:
                printer.warning('Looking for usage of', full_path)
            if self.is_unused(short_path):
                unused.append(entry)
        return unused

    def is_unused(self, short_path):
        if self.is_excluded(short_path):
            return False
        for file_name in self.all_files:
            with open(file_name, encoding='utf-8') as fp:
                try:
                    contents = fp.read()
                except UnicodeDecodeError:
                    printer.error('Could not read file:', file_name, '(skipping)')
            if short_path in contents:
                return False
        return True

    def get_files_to_check(self, where):
        files = []
        for dir_ in where:
            if not os.path.isdir(dir_):
                raise NotADirectoryError(dir_)
            sub_dirs = []
            for base_name in os.listdir(dir_):
                full_path = os.path.join(dir_, base_name)
                if os.path.isfile(full_path):
                    if not self.is_ignored_file(full_path):
                        files.append(full_path)
                elif os.path.isdir(full_path):
                    if not self.is_ignored_dir(full_path):
                        sub_dirs.append(full_path)
            if sub_dirs:
                files.extend(self.get_files_to_check(sub_dirs))
        return files

    def get_source_dirs(self, where):
        dirs = []
        for base_name in os.listdir(where):
            full_path = os.path.join(where, base_name)
            skip = (
                not os.path.isdir(full_path) or
                self.is_ignored_dir(full_path)
            )
            if not skip:
                if base_name == 'templates':
                    dirs.append(full_path)
                else:
                    dirs.extend(self.get_source_dirs(full_path))
        return dirs

    def get_source_files(self, template_dirs):
        files = []
        for dir_ in template_dirs:
            for base_name in os.listdir(dir_):
                full_path = os.path.join(dir_, base_name)
                if os.path.isdir(full_path):
                    files.extend(self.get_source_files([full_path]))
                elif os.path.isfile(full_path):
                    short_path = os.path.relpath(full_path, os.path.dirname(dir_))
                    d, *rest = os.path.split(short_path)
                    if d == 'templates':
                        short_path = os.path.join(*rest)
                    files.append((full_path, short_path, base_name))
        return files

    def is_ignored_dir(self, full_path):
        if full_path in (settings.MEDIA_ROOT, settings.STATIC_ROOT):
            if self.debug:
                printer.warning('Ignoring media root', full_path)
            return True
        for dir_ in self.where:
            if full_path == os.path.join(dir_, 'media'):
                if self.debug:
                    printer.warning('Ignoring top level media directory', full_path)
                return True
        base_name = os.path.basename(full_path)
        return any(fnmatch.fnmatch(base_name, p) for p in self.ignore_dirs)

    def is_ignored_file(self, full_path):
        base_name = os.path.basename(full_path)
        type_, _ = mimetypes.guess_type(base_name)
        name, ext = os.path.splitext(base_name)
        included = (
            (type_ is None and ext in ['.cfg', '.ini', '.mk', '.yml', '.yaml']) or
            (type_ is None and base_name.startswith('Makefile')) or
            (type_ is not None and type_.startswith('text/')) or
            (type_ is not None and type_ == 'application/javascript') or
            (type_ is not None and type_ == 'application/json')
        )
        # XXX: Special case
        if 'bpython/test/fodder/encoding_latin1.py' in full_path:
            included = False
        if not included:
            if self.debug:
                printer.warning('Ignoring file', full_path, 'with MIME type', type_)
            return True
        return any(fnmatch.fnmatch(base_name, p) for p in self.ignore_files)

    def is_excluded(self, short_path):
        app_dir, *_ = os.path.split(short_path)
        return any(fnmatch.fnmatch(app_dir, p) for p in self.exclude)
