from django.apps import AppConfig


class UnregisteredModelsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "unregistered_models"
