from __future__ import absolute_import
from .forms import BaseFormSet, BaseModelFormSet  # noqa
from .db import dictfetchall, will_be_deleted_with, ChoiceEnum  # noqa


DEFAULT_FEATURES = {
    'templatetags': True,
    'clear_expired_sessions': True,
    'warn_on_invalid_email_during_password_reset': True,
    'add_css_classes_to_forms': True,
}

default_app_config = 'arcutils.apps.ARCUtilsConfig'
