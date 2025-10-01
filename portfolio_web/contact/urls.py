from django.urls import path

from . import views

app_name = "contact"

urlpatterns = [
    path("", views.contact_index, name="contact_index"),
]
