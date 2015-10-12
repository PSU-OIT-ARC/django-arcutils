from __future__ import absolute_import

# Django verions 1.6 and worse don't have the "apps" package so we have to mock
# it up when its not available
try:
    from django.apps import AppConfig, apps
    is_installed = apps.is_installed
except ImportError:
    class AppConfig:
        pass

    def is_installed(dotted_app_path):
        from django.conf import settings
        return dotted_app_path in settings.INSTALLED_APPS

from . import DEFAULT_FEATURES


class ARCUtilsConfig(AppConfig):
    name = "arcutils"

    def ready(self):
        """
        Do a bunch of monkey patching based on the ARCUTILS_FEATURES setting
        """
        from django.conf import settings
        ARCUTILS_FEATURES = getattr(settings, 'ARCUTILS_FEATURES', DEFAULT_FEATURES)

        # monkey patch the PasswordResetForm so it indicates if a user does not exist
        if ARCUTILS_FEATURES.get('warn_on_invalid_email_during_password_reset'):
            from django.contrib.auth.forms import PasswordResetForm

            original_clean_email = getattr(PasswordResetForm, "clean_email", lambda self: self.cleaned_data['email'])
            def _clean_email(self):
                from django.contrib.auth import get_user_model
                email = self.cleaned_data['email']
                UserModel = get_user_model()
                if not UserModel.objects.filter(email=email, is_active=True).exists():
                    raise forms.ValidationError("A user with that email address does not exist!")

                return original_clean_email(self)

            PasswordResetForm.clean_email = _clean_email

        # hook up the session clearer
        CLEAR_EXPIRED_SESSIONS_AFTER_N_REQUESTS = getattr(settings, 'CLEAR_EXPIRED_SESSIONS_AFTER_N_REQUESTS', 100)
        CLEAR_EXPIRED_SESSIONS_ENABLED = is_installed('django.contrib.sessions') and CLEAR_EXPIRED_SESSIONS_AFTER_N_REQUESTS is not None
        if ARCUTILS_FEATURES.get('clear_expired_sessions') and CLEAR_EXPIRED_SESSIONS_ENABLED:
            from .sessions import patch_sessions

            patch_sessions(CLEAR_EXPIRED_SESSIONS_AFTER_N_REQUESTS)

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
