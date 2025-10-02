from django.contrib import admin

from .models import ContactMessage


# Register your models here.
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_resolved", "created_at")
    list_filter = ("is_resolved", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("created_at",)
