from django.apps import AppConfig


class SingletonModelsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "singleton_models"
