"""Add current request to thread local storage.

API:

    - :class:`ThreadLocalMiddleware`: add this to MIDDLEWARE_CLASSES
    - :func:`get_current_request`
    - :func:`get_current_user`: use as model field default

This was added with a single purpose in mind: to automate the setting of
created-by and updated-by model fields in a request context. E.g.::

    class MyModel(models.Model):

        created_by = models.ForeignKey('auth.User', default=get_current_user)
        updated_by = models.ForeignKey('auth.User', default=get_current_user)

    @receiver(pre_save, sender=MyModel)
    def set_updated_by(sender, instance, **kwargs):
        if not instance.updated_by:
            user = get_current_user()
            if user is not None:
                instance.updated_by = user

Note that in a non-request context such as a management command, the
current request won't be saved to thread local storage and both API
functions will return ``None``, hence the check for ``None`` in the
receiver above.

This approach ensures the created-by and updated-by fields are set on
the relevant models regardless of which views they're used in.

"""
import logging
import threading

from .middleware import MiddlewareBase


log = logging.getLogger(__name__)


class _ThreadLocalStorage(threading.local):

    def get(self, name, default=None):
        if hasattr(self, name):
            return getattr(self, name)
        log.warning('%s has not been saved to thread local storage', name)
        return default

    def put(self, name, value):
        setattr(self, name, value)

    def remove(self, name):
        if hasattr(self, name):
            delattr(self, name)


_thread_local_storage = _ThreadLocalStorage()


def get_current_request(default=None):
    """Don't use this unless you have a REALLY good reason."""
    return _thread_local_storage.get('request', default)


def get_current_user(default=None):
    """Don't use this unless you have a REALLY good reason."""
    request = _thread_local_storage.get('request')
    if request is None:
        return default
    return request.user


class ThreadLocalMiddleware(MiddlewareBase):

    def before_view(self, request):
        _thread_local_storage.put('request', request)

    def after_view(self, request, response):
        _thread_local_storage.remove('request')

    def process_exception(self, request, exception):
        _thread_local_storage.remove('request')
