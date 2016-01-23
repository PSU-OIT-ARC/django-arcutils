import datetime
import fcntl
import logging
import multiprocessing
import os
import sched
import time

from .decorators import cached_property


ONE_DAY = datetime.timedelta(days=1)


class DailyTasksProcess(multiprocessing.Process):

    """A simple daily task runner.

    .. note:: If your needs are more complex than running more than a
              handful of daily tasks, you probably shouldn't use this.

    This is an alternative to cron and Celery. The former is hard to get
    set up on ARC VMs; the latter is overkill when you just need to run
    a task or two once a day (and adds more points of failure).

    Now, it can certainly be argued that this adds complexity and is
    non-standard. On the other hand, what we've seen in practice are
    several different kinds of workarounds (AKA hacks) for the "run a
    couple of daily tasks without massive pain" problem. This at least
    provides *one* recommended way of running daily tasks.

    This is used by adding the following to the *bottom* of a project's
    wsgi.py::

        if not settings.DEBUG:
            from arcutils.tasks import DailyTasksProcess
            daily_tasks = DailyTasksProcess(home=root)
            # Rebuild the search index at 3:01am every day
            daily_tasks.add_task(call_command, 3, 1, ('rebuild_index',), {'interactive': False})
            daily_tasks.start()

    .. note:: :func:`django.core.wsgi.get_wsgi_application` *should* be
              called before adding tasks to ensure the environment is
              fully configured before any tasks are run.

    .. note:: In production, multiple mod_wsgi processes may be started,
              and each of them will execute the code as shown above, but
              only *one* of those mod_wsgi process will initialize a
              :class:`DailyTasksProcess` to run the specified tasks.

    """

    def __init__(self, *args, home=None, lock_file_path=None, daemon=True, **kwargs):
        super().__init__(*args, daemon=daemon, **kwargs)
        home = home or os.getcwd()

        if lock_file_path is None:
            lock_file_name = '.{cls.__module__}.{cls.__qualname__}.lock'.format(cls=self.__class__)
            lock_file_path = os.path.join(home, lock_file_name)

        self.home = home
        self.lock_file_path = lock_file_path
        self.lock_file = open(self.lock_file_path, 'w')

        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # Already locked; some other process is running daily tasks.
            self.add_task = self._noop
            self.start = self._noop
            self.lock_file.close()
        else:
            self.scheduler = sched.scheduler(time.time)

    @cached_property
    def log(self, *args, **kwargs):
        return logging.getLogger(__name__)

    def add_task(self, task, hour, minute=0, args=(), kwargs=None, name=None):
        """Add a task to be run daily at the given hour and minute.

        ``hour`` must be an int between 0 and 23 (inclusive).

        ``minute`` must be an int between 0 and 59 (inclusive).

        ``task`` will be called as ``task(*args, **kwargs)``.

        ``name`` is a display name for the task; it's shown in log
        messages. If a ``name`` isn't passed, this will default to
        ``task.__name__``.

        """
        name = name or task.__name__

        log = self.log
        log.info('Adding daily task %s at %d:%d', name, hour, minute)

        assert isinstance(hour, int), 'hour must be an int'
        assert 0 <= hour < 24, 'hour must be in [0, 23]'
        assert isinstance(minute, int), 'minute must be an int'
        assert 0 <= minute < 60, 'hour must be in [0, 59]'

        now = datetime.datetime.now()
        date_part = now.date()
        time_part = datetime.time(hour, minute, 0, 0)
        scheduled_time = datetime.datetime.combine(date_part, time_part)

        if scheduled_time <= now:
            scheduled_time += ONE_DAY

        log.info('First run of %s will be at %s', name, scheduled_time)

        kwargs = {} if kwargs is None else kwargs

        def action():
            nonlocal scheduled_time
            log.info('Running task %s with %s and %s...', name, args, kwargs)
            task(*args, **kwargs)
            scheduled_time += ONE_DAY
            log.info('Rescheduling %s for %s', name, scheduled_time)
            self.scheduler.enterabs(scheduled_time.timestamp(), None, action)

        self.scheduler.enterabs(scheduled_time.timestamp(), None, action)

    def run(self):
        self.lock_file.write(str(self.pid))
        self.lock_file.write('\n')
        self.lock_file.flush()
        try:
            if self.scheduler.empty():
                raise RuntimeError(
                    'No tasks have been added; one or more tasks must be added via add_task() '
                    'before start() is called')
            self.scheduler.run()
        finally:
            fcntl.flock(self.lock_file, fcntl.LOCK_UN)
            self.lock_file.close()
            os.remove(self.lock_file_path)

    def _noop(self, *args, **kwargs):
        pass
