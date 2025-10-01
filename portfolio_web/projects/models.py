# projects/models.py
from django.db import models


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    featured = models.BooleanField(default=False)  # <- this is the db field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional: keep a readable attribute for templates/Python (NOT for queries)
    @property
    def is_featured(self):
        return self.featured

    def __str__(self):
        return self.title
