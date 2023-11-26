import sys
from datetime import datetime

from django.apps import AppConfig


class StoremonitoringsystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps"
    current_timestamp = datetime.strptime(
        "2023-01-25 18:13:22.479220", "%Y-%m-%d %H:%M:%S.%f"
    )

    def ready(self):
        from .utils.import_data import import_data
        from .utils.is_importing import set_is_importing

        set_is_importing(False)

        if "runserver" in sys.argv:
            import_data()
