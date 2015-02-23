from random import random
import logging

from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.core.signals import request_started

logger = logging.getLogger(__name__)


def clear_expired_sessions(sender, **kwargs):
    """
    Triggered by the request_started signal, this function calls the
    clear_expired method on the session backend, with a certain probability
    (similar to how PHP clears sessions)
    """
    if random() <= clear_expired_sessions.probability:
        try:
            clear_expired_sessions.engine.SessionStore.clear_expired()
            logger.debug('Sessions cleared')
        except NotImplementedError:
            logger.debug('Session engine "%s" does ont support clearing expired sessions.' % settings.SESSION_ENGINE)


def patch_sessions(num_requests):
    """
    Connects the clear_expired_sessions function to the request_started signal,
    and does a little configuration calculations and checking.
    """

    if num_requests < 1:
        raise ImproperlyConfigured('The num_requests setting must be > 0')

    clear_expired_sessions.engine = import_module(settings.SESSION_ENGINE)
    clear_expired_sessions.probability = 1.0 / num_requests
    request_started.connect(clear_expired_sessions)
