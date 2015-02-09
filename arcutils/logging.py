import logging.config
from . import LOGSTASH_ADDRESS

def basic(_):
    """
    Logs to the console always, and to LOGSTASH_ADDRESS when DEBUG is off. Overrides
    Django's logging.

    To use, add to your settings file:
    LOGGING_CONFIG = 'arcutils.logging.basic'

    We ignore the configuration that is passed in, hence the _ as the first
    argument
    """
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(pathname)s:%(lineno)d %(message)s'
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
                'host': LOGSTASH_ADDRESS.rsplit(":", 1)[0],
                'port': int(LOGSTASH_ADDRESS.rsplit(":", 1)[1]),
                'version': 1,
                'message_type': 'django',
                'filters': ['require_debug_false'],
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler',
                'include_html': True
            }
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
    })
