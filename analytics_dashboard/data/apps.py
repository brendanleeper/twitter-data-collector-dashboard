from django.apps import AppConfig
from .collector import Collector
import os
import sys

class DataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data'

    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            if 'runserver' in sys.argv:
                c = Collector()
                c.start()
