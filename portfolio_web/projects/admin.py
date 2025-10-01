# projects/admin.py
from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "featured", "created_at")
    list_filter = ("featured", "created_at")
    search_fields = ("title", "slug", "description")
    ordering = ("-created_at",)
