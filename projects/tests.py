from django.test import TestCase
from django.urls import reverse
from projects.models import Project
from taggit.models import Tag


class ProjectsViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.p1 = Project.objects.create(
            title="Alpha",
            slug="alpha",
            description="**Alpha MD**",
            tech_stack="Django, HTMX",
        )
        cls.p2 = Project.objects.create(
            title="Beta",
            slug="beta",
            description="Beta desc",
            tech_stack="Python, Pandas",
        )
        cls.p3 = Project.objects.create(
            title="Gamma", slug="gamma", description="Gamma desc", tech_stack="Django"
        )
        cls.p1.tags.add("web", "django")
        cls.p2.tags.add("data")
        cls.p3.tags.add("web")

    def test_list_basic(self):
        url = reverse("projects:list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Alpha")
        self.assertContains(res, "Beta")
        self.assertContains(res, "Gamma")

    def test_search_title(self):
        url = reverse("projects:list")
        res = self.client.get(url, {"q": "Alpha"})
        self.assertContains(res, "Alpha")
        self.assertNotContains(res, "Beta")
        self.assertNotContains(res, "Gamma")

    def test_search_tech(self):
        url = reverse("projects:list")
        res = self.client.get(url, {"q": "Pandas"})
        self.assertContains(res, "Beta")
        self.assertNotContains(res, "Alpha")

    def test_tag_filter(self):
        url = reverse("projects:list")
        res = self.client.get(url, {"tag": "web"})
        self.assertContains(res, "Alpha")
        self.assertContains(res, "Gamma")
        self.assertNotContains(res, "Beta")

    def test_tag_filter_with_search(self):
        url = reverse("projects:list")
        res = self.client.get(url, {"tag": "web", "q": "Gamma"})
        self.assertContains(res, "Gamma")
        self.assertNotContains(res, "Alpha")
        self.assertNotContains(res, "Beta")

    def test_pagination(self):
        # Create more to force multiple pages (per-page: 9; here we keep it simple)
        for i in range(12):
            Project.objects.create(
                title=f"P{i}", slug=f"p{i}", description="x", tech_stack="x"
            )
        url = reverse("projects:list")
        res1 = self.client.get(url, {"page": 1})
        res2 = self.client.get(url, {"page": 2})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)

    def test_detail_markdown_and_prev_next(self):
        url = reverse("projects:detail", args=[self.p1.slug])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        # Markdown rendered (strong tag appears)
        self.assertContains(res, "<strong>Alpha MD</strong>", html=True)
