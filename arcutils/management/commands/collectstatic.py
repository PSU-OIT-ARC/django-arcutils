import os
from collections import OrderedDict

from django.core.management.base import CommandError
from django.contrib.staticfiles.finders import get_finders
from django.contrib.staticfiles.utils import matches_patterns
from django.contrib.staticfiles.management.commands.collectstatic import Command as BaseCommand


class Command(BaseCommand):

    help = (
        'Collect static files in a single location. '
        'Adds additional exclude/include capabilities to the built in collectstatic command.'
    )

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--exclude', action='append', default=[], dest='exclude_patterns', metavar='PATTERN',
            help='Exclude files based on patterns; '
                 'matches against entire (relative) path; '
        )
        parser.add_argument(
            '--include', action='append', default=[], dest='include_patterns', metavar='PATTERN',
            help='Include files based on patterns; '
                 'matches against entire (relative) path; '
                 'takes precedence over --exclude'
        )

    def set_options(self, **options):
        super().set_options(**options)
        self.include_patterns = options['include_patterns']
        self.exclude_patterns = options['exclude_patterns']

    def collect(self):
        # Only invoke our custom include/exclude logic if indicated.
        if not (self.include_patterns or self.exclude_patterns):
            return super().collect()

        # Django's version of this command doesn't provide many hooks
        # for customizing the collection process, so this method is
        # a copy of the base collect method with a couple tweaks to
        # override ignore/exclude/include logic.

        if self.symlink and not self.local:
            raise CommandError("Can't symlink to a remote destination.")

        if self.clear:
            self.clear_dir('')

        handler = self.link_file if self.symlink else self.copy_file

        found_files = OrderedDict()

        for finder in get_finders():
            for path, storage in finder.list([]):
                if self.include_path(path):
                    prefix = getattr(storage, 'prefix', None)
                    prefixed_path = os.path.join(prefix, path) if prefix else path
                    if prefixed_path not in found_files:
                        found_files[prefixed_path] = (storage, path)
                        handler(path, prefixed_path, storage)

        if self.post_process and hasattr(self.storage, 'post_process'):
            processor = self.storage.post_process(found_files, dry_run=self.dry_run)
            for original_path, processed_path, processed in processor:
                if isinstance(processed, Exception):
                    self.stderr.write("Post-processing '%s' failed!" % original_path)
                    self.stderr.write('')
                    raise processed
                if processed:
                    self.log(
                        "Post-processed '%s' as '%s'" % (original_path, processed_path), level=1)
                    self.post_processed_files.append(original_path)
                else:
                    self.log("Skipped post-processing '%s'" % original_path)

        return {
            'modified': self.copied_files + self.symlinked_files,
            'unmodified': self.unmodified_files,
            'post_processed': self.post_processed_files,
        }

    def include_path(self, path):
        include = True
        if self.ignore(path) or self.exclude(path):
            include = False
            if self.include(path):
                include = True
        return include

    def ignore(self, path):
        for segment in self.split_path(path):
            if matches_patterns(segment, self.ignore_patterns):
                return True
        return False

    def exclude(self, path):
        return matches_patterns(path, self.exclude_patterns)

    def include(self, path):
        return matches_patterns(path, self.include_patterns)

    @staticmethod
    def split_path(path):
        assert not os.path.isabs(path), 'Expecting relative path; got %s' % path
        segments = []
        path = os.path.normpath(path)
        _, path = os.path.splitdrive(path)
        head, tail = os.path.split(path)
        while tail:
            segments.append(tail)
            head, tail = os.path.split(head)
        return reversed(segments)
