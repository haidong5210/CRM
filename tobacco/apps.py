from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class WebmasterConfig(AppConfig):
    name = 'tobacco'

    def ready(self):
        autodiscover_modules('ad')
