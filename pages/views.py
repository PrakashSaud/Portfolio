from blog.models import BlogPost
from django.shortcuts import render
from projects.models import Project


def home(request):
    featured_projects = Project.objects.filter(featured=True).order_by("-created_at")[
        :6
    ]
    latest_posts = BlogPost.objects.all().order_by("-created_at")[:3]
    return render(
        request,
        "pages/home.html",
        {
            "featured_projects": featured_projects,
            "latest_posts": latest_posts,
        },
    )


def about(request):
    return render(request, "pages/about.html")


# error handlers (wired later in root urls.py)
def handler404(request, exception):
    return render(request, "pages/404.html", status=404)


def handler500(request):
    return render(request, "pages/500.html", status=500)
