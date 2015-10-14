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
