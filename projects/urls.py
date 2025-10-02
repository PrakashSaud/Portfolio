# projects/urls.py
from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    path("", views.projects_list, name="list"),              # main list w/ search & filters
    path("index/", views.project_index, name="project_index"),  # optional landing page
    path("<slug:slug>/", views.project_detail, name="detail"),
]