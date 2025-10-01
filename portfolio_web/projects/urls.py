from django.urls import path
from django.views.generic import TemplateView

app_name = "projects"

urlpatterns = [
    path(
        "",
        TemplateView.as_view(template_name="projects/projectindex.html"),
        name="project_index",
    ),
    path(
        "<int:pk>/",
        TemplateView.as_view(template_name="projects/detail.html"),
        name="project_detail",
    ),
]
