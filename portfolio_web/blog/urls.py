from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "blog"

urlpatterns = [
    path(
        "",
        TemplateView.as_view(template_name="blog/blog_index.html"),
        name="blog_index",
    ),
    path("<slug:slug>/", views.BlogPostDetailView.as_view(), name="blog_detail_slug"),
]
