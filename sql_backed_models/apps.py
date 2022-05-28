from django.apps import AppConfig


class SqlBackedModelsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sql_backed_models"
