# pages/views.py
from blog.models import BlogPost
from django.shortcuts import render
from projects.models import Project


def home(request):
    featured_projects = Project.objects.filter(is_featured=True)[:6]
    latest_posts = BlogPost.objects.order_by("-created_at")[:3]
    return render(
        request,
        "pages/home.html",
        {"featured_projects": featured_projects, "latest_posts": latest_posts},
    )


def about(request):
    return render(request, "pages/about.html")
