import logging.config
import pkg_resources
from copy import copy

from django.conf import settings

# Make sure a NullHandler is available
# This was added in Python 2.7/3.2
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

# Make sure that dictConfig is available
# This was added in Python 2.7/3.2
try:
    from logging.config import dictConfig
except ImportError:
    from django.utils.dictconfig import dictConfig


# set the default place to send logs, and a CA cert file. Since logs.rc.pdx.edu
# has a cert signed by signed by PSUCA, that's the CA we're going to use
LOGSTASH_ADDRESS = getattr(settings, 'LOGSTASH_ADDRESS', 'logs.rc.pdx.edu:5043')
LOGSTASH_HOST, LOGSTASH_PORT = LOGSTASH_ADDRESS.rsplit(':', 1)
LOGSTASH_PORT = int(LOGSTASH_PORT)
LOGSTASH_CA_CERTS = getattr(settings, 'LOGSTASH_CA_CERTS', pkg_resources.resource_filename('arcutils', 'PSUCA.crt'))


DEFAULT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s %(pathname)s:%(lineno)d %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S',
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'logstash': {
            'level': 'INFO',
            'class': 'stashward.StashwardHandler',
            'host': LOGSTASH_HOST,
            'port': LOGSTASH_PORT,
            'ca_certs': LOGSTASH_CA_CERTS,
            'message_type': 'django',
            'filters': ['require_debug_false'],
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'null': {
            'class': 'arcutils.logging.NullHandler',
        },
    },
    'loggers': {
        # we need to explicitly override the django logger so it propagates
        # to the root logger
        'django': {
            'propagate': True,
        },
        'elasticsearch': {
            'level': 'ERROR',
        }
    },
    'root': {
        'handlers': ['console', 'mail_admins', 'logstash'],
        'level': 'INFO',
    },
}


def basic(config):
    """Log to the console always and to Logstash when DEBUG is off.

    Overrides Django's logging.

    The default config is defined in :const:`DEFAULT_CONFIG`.

    To use, add the following to your settings file::

        LOGGING_CONFIG = 'arcutils.logging.basic'

    If you set the `LOGGING` setting (as a dict that could be passed to
    :func:`logging.config.dictConfig`), that config will be passed to
    this function as the ``config`` arg. Any such config will be merged
    into `DEFAULT_CONFIG` and will take precedence over the defaults.
    For example, you might set `LOGGING_CONFIG` like so to stop those
    annoying ALLOWED_HOSTS errors::

        LOGGING = {
            'loggers': {
                'django.security.DisallowedHost': {
                    'handlers': ['null'],
                    'propagate': false
                },
            }
        }

    .. note:: The above isn't enabled by default because you should be
              really sure your ALLOWED_HOSTS setting is correct before
              ignoring these errors.

    """
    config = _merge(DEFAULT_CONFIG, config)
    dictConfig(config)


def _merge(d, e):
    """Merge dict ``e`` into dict ``d``."""
    d = copy(d)
    for k, v in e.items():
        if k in d and isinstance(v, dict):
            v = _merge(d[k], v)
        else:
            v = copy(v)
        d[k] = v
    return d
