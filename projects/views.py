# portfolio_web/projects/views.py
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from taggit.models import Tag

from .models import Project


def project_index(request):
    """
    Renders the main static Projects landing page.
    Currently uses sample data aligned with the new frontend layout.
    Later, this can be connected to the Project model dynamically.
    """
    projects = [
        {
            "title": "Hotel Staff Scheduling Optimization",
            "description": "Machine learning project using optimization models to minimize operational costs and align with employee preferences.",
            "image": "img/project1.jpg",
            "category": "Data Science",
            "category_color": "blue",
            "link": "#",
        },
        {
            "title": "Stock Prediction & Sentiment Analysis",
            "description": "Python and NLP project analyzing financial news to predict demand, supply, and price movement.",
            "image": "img/project2.jpg",
            "category": "AI / NLP",
            "category_color": "green",
            "link": "#",
        },
        {
            "title": "FocusFlow — Unified Smart Inbox",
            "description": "SaaS productivity tool integrating multiple communication channels with AI summarization and prioritization.",
            "image": "img/project3.jpg",
            "category": "Web App",
            "category_color": "purple",
            "link": "focusflow:index",
        },
    ]

    context = {"projects": projects}
    return render(request, "projects/project_index.html", context)


def projects_list(request):
    """
    Works without JS; HTMX enhances filtering/pagination.
    Query params:
      - q: search across title, tech_stack
      - tag: single tag slug to filter
      - page: paginator page
    """
    q = request.GET.get("q", "").strip()
    tag_slug = request.GET.get("tag", "").strip()
    queryset = Project.objects.all()

    if q:
        queryset = queryset.filter(Q(title__icontains=q) | Q(tech_stack__icontains=q))
    active_tag = None
    if tag_slug:
        active_tag = get_object_or_404(Tag, slug=tag_slug)
        queryset = queryset.filter(tags__in=[active_tag]).distinct()

    paginator = Paginator(queryset, 9)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "q": q,
        "active_tag": active_tag,
        "all_tags": Tag.objects.all().order_by("name"),
    }

    # HTMX partial update (only the grid + pager)
    if request.headers.get("HX-Request"):
        return render(request, "projects/_projects_grid.html", context)
    return render(request, "projects/project_list.html", context)


def project_detail(request, slug):
    project = get_object_or_404(Project)
    # prev/next by created_at (Meta.ordering is -created_at)
    prev_project = (
        Project.objects.filter(created_at__gt=project.created_at)
        .order_by("created_at")
        .first()
    )
    next_project = (
        Project.objects.filter(created_at__lt=project.created_at)
        .order_by("-created_at")
        .first()
    )
    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "prev_project": prev_project,
            "next_project": next_project,
        },
    )