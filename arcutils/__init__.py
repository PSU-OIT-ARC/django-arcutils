from .forms import BaseFormSet, BaseModelFormSet  # noqa
from .db import dictfetchall, will_be_deleted_with, ChoiceEnum  # noqa


DEFAULT_FEATURES = {
    'add_css_classes_to_forms': True,
}

default_app_config = 'arcutils.apps.ARCUtilsConfig'
