from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager


class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    tech_stack = models.CharField(
        max_length=300, help_text="Comma-separated or free text"
    )
    cover_image = models.ImageField(upload_to="projects/", blank=True, null=True)
    repo_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    status = models.CharField(max_length=50, default="active")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    eatured = models.BooleanField(default=False)
    tags = TaggableManager(blank=True)

    def get_absolute_url(self):
        return reverse("projects:detail", args=[self.slug])

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
