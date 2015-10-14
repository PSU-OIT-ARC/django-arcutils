from django.apps import AppConfig, apps
is_installed = apps.is_installed

from . import DEFAULT_FEATURES


class ARCUtilsConfig(AppConfig):
    name = "arcutils"

    def ready(self):
        """
        Do a bunch of monkey patching based on the ARCUTILS_FEATURES setting
        """
        from django.conf import settings
        ARCUTILS_FEATURES = getattr(settings, 'ARCUTILS_FEATURES', DEFAULT_FEATURES)

        # add all the templatetag libraries we want available by default
        if ARCUTILS_FEATURES.get('templatetags'):
            from django.template.base import add_to_builtins

            add_to_builtins('django.contrib.staticfiles.templatetags.staticfiles')
            # add the arc template tags to the builtin tags
            add_to_builtins('arcutils.templatetags.arc')

        # make the `required_css_class` attribute for forms and fields
        # "required" by default
        if ARCUTILS_FEATURES.get('add_css_classes_to_forms'):
            from django.forms.fields import Field
            from django import forms

            forms.Form.required_css_class = "required"
            forms.ModelForm.required_css_class = "required"
            Field.required_css_class = "required"
