from django.contrib import admin
from django.utils.html import format_html

from .models import Project


# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("thumb", "title", "status", "featured", "order", "created_at")
    list_filter = ("status", "featured", "created_at")
    search_fields = ("title", "description", "tech_stack", "repo_url", "live_url")
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("order", "-created_at")

    @admin.display(description="", ordering="id")
    def thumb(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" '
                'style="height:45px;width:80px;object-fit:cover;border-radius:6px;" />',
                obj.cover_image.url,
            )
        return "—"
