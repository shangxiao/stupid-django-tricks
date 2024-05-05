from django.urls import path

from .views import bulk_create_users, bulk_create_users_js

urlpatterns = [
    path("bulk_create_form/", bulk_create_users),
    path("bulk_create_form_js/", bulk_create_users_js),
    path("bulk_create_form_js/<int:pk>/", bulk_create_users_js),
]
