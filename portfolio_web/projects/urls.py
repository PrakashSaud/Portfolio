from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "projects"

urlpatterns = [
    path(
        "",
        TemplateView.as_view(template_name="projects/project_index.html"),
        name="project_index",
    ),
    # path(
    #     "<int:pk>/",
    #     TemplateView.as_view(template_name="projects/detail.html"),
    #     name="project_detail",
    # ),
    path("<slug:slug>/", views.ProjectDetailView.as_view(), name="project_detail_slug"),
]
