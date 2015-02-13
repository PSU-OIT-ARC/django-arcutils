from copy import copy
import logging.config

from . import LOGSTASH_ADDRESS


LOGSTASH_HOST, LOGSTASH_PORT = LOGSTASH_ADDRESS.rsplit(':', 1)
LOGSTASH_PORT = int(LOGSTASH_PORT)


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
            'class': 'logstash.TCPLogstashHandler',
            'host': LOGSTASH_HOST,
            'port': LOGSTASH_PORT,
            'version': 1,
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
            'class': 'logging.NullHandler',
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
    For example, to configure a logger for your app, you might set
    `LOGGING_CONFIG` like so::

        LOGGING_CONFIG = {
            'loggers': {
                'rethink': {
                    'level': 'DEBUG'
                }
            }
        }

    """
    config = _merge(DEFAULT_CONFIG, config)
    return logging.config.dictConfig(config)


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
