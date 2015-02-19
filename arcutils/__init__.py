from __future__ import print_function
from __future__ import absolute_import
import random, datetime
import logging
import os
import pkg_resources

from django.conf import settings

logger = logging.getLogger(__name__)


DEFAULT_FEATURES = {'templatetags': True, 'sessions': True, 'forms': True, 'db': True}
ARCUTILS_FEATURES = getattr(settings, 'ARCUTILS_FEATURES', DEFAULT_FEATURES)

# set the default place to send logs, and a CA cert file. Since logs.rc.pdx.edu
# has a cert signed by signed by PSUCA, that's the CA we're going to use
LOGSTASH_ADDRESS = getattr(settings, "LOGSTASH_ADDRESS", 'logs.rc.pdx.edu:5043')
LOGSTASH_CA_CERTS = getattr(settings, "LOGSTASH_CA_CERTS", pkg_resources.resource_filename('arcutils', "PSUCA.crt"))

CLEAR_EXPIRED_SESSIONS_AFTER_N_REQUESTS = getattr(settings, 'CLEAR_EXPIRED_SESSIONS_AFTER_N_REQUESTS', 100)
CLEAR_EXPIRED_SESSIONS_ENABLED = \
    'django.contrib.sessions' in settings.INSTALLED_APPS and CLEAR_EXPIRED_SESSIONS_AFTER_N_REQUESTS is not None

if ARCUTILS_FEATURES.get('templatetags'):
    from django.template import add_to_builtins

    add_to_builtins('django.contrib.staticfiles.templatetags.staticfiles')
    # add the arc template tags to the builtin tags, and the bootstrap tag
    add_to_builtins('arcutils.templatetags.arc')
    add_to_builtins('arcutils.templatetags.bootstrap')

if ARCUTILS_FEATURES.get('sessions') and CLEAR_EXPIRED_SESSIONS_ENABLED:
    from .sessions import patch_sessions

    patch_sessions(CLEAR_EXPIRED_SESSIONS_AFTER_N_REQUESTS)

if ARCUTILS_FEATURES.get('forms'):
    import .forms

if ARCUTILS_FEATURES.get('db'):
    from .db import dictfetchall, will_be_deleted_with, ChoiceEnum
