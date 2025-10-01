from django.contrib import admin
from django.utils.html import format_html

from .models import BlogPost


# Register your models here.
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("thumb", "title", "status", "published_at", "created_at")
    list_filter = ("status", "published_at", "created_at")
    search_fields = ("title", "excerpt", "content", "tags")
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"

    @admin.display(description="", ordering="id")
    def thumb(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="height:45px;width:80px;object-fit:cover;border-radius:6px;" />',
                obj.cover_image.url,
            )
        return "—"
