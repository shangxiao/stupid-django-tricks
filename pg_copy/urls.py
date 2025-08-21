from django.urls import path

from .views import export, export_traditional, json, json_traditional

urlpatterns = [
    path("export/", export),
    path("export-traditional/", export_traditional),
    path("json/", json),
    path("json-traditional/", json_traditional),
]
