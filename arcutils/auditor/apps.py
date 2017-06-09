import importlib

from django.apps import AppConfig


class DefaultAppConfig(AppConfig):

    name = 'arcutils.auditor'

    def ready(self):
        signals = importlib.import_module('.signals', package=self.name)
        signals.connect(self)
