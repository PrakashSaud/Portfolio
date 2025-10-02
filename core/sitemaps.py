from blog.models import Post
from django.contrib.sitemaps import Sitemap
from projects.models import Project


class ProjectSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Project.objects.all()

    def lastmod(self, obj):
        return obj.updated_at


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Post.objects.all()

    def lastmod(self, obj):
        return obj.updated_at
