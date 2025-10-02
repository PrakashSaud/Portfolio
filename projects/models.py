# projects/models.py
from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # tags (using django-taggit)
    tags = TaggableManager(blank=True)

    @property
    def is_featured(self):
        return self.featured

    def get_absolute_url(self):
        return reverse("projects:detail", args=[self.slug])

    def get_previous(self):
        return (
            Project.objects.filter(created_at__lt=self.created_at)
            .order_by("-created_at")
            .first()
        )

    def get_next(self):
        return (
            Project.objects.filter(created_at__gt=self.created_at)
            .order_by("created_at")
            .first()
        )

    def __str__(self):
        return self.title