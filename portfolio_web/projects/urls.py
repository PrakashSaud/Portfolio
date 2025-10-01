from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_index, name="project_index"),
    path("<slug:slug>/", views.project_detail, name="detail"),
]
