from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.core.signals import request_started
from django.contrib.auth import get_user_model
from django.dispatch import receiver


def patch_sessions(num_requests):
    if num_requests < 1:
        raise ImproperlyConfigured('The num_requests setting must be > 0')

    @receiver(request_started)
    def clear_expired_sessions(sender, **kwargs):
        if random.random() <= clear_expired_sessions.probability:
            try:
                clear_expired_sessions.engine.SessionStore.clear_expired()
                logger.debug('Sessions cleared')
            except NotImplementedError:
                logger.debug('Session engine "%s" does ont support clearing expired sessions.' % settings.SESSION_ENGINE)

    clear_expired_sessions.engine = import_module(settings.SESSION_ENGINE)
    clear_expired_sessions.probability = 1.0 / num_requests
