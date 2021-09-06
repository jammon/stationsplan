from django.apps import AppConfig


class StationsplanAppConfig(AppConfig):
    name = "sp_app"
    verbose_name = "Stationsplan App"

    def ready(self):
        import sp_app.signals
