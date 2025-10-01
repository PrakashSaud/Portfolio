from django.urls import path
from django.views.generic import TemplateView

app_name = "blog"

urlpatterns = [
    path(
        "",
        TemplateView.as_view(template_name="blog/blog_index.html"),
        name="blog_index",
    ),
]
