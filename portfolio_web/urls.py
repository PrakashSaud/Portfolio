"""
URL configuration for portfolio_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("pages.urls", "pages"), namespace="pages")),
    path("projects/", include(("projects.urls", "projects"), namespace="projects")),
    path("blog/", include(("blog.urls", "blog"), namespace="blog")),
    path("contact/", include(("contact.urls", "contact"), namespace="contact")),
    path("focusflow/", include(("apps.focusflow.urls", "focusflow"), namespace="focusflow")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# error handlers
handler404 = "pages.views.handler404"
handler500 = "pages.views.handler500"
