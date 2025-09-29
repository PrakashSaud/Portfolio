from django.shortcuts import render

# Create your views here.
def home(request):
    """
    Renders the site landing page.
    Why function-based view (FBV)?
    - Simple pages are clearer as FBVs; fewer moving parts for beginners.
    Alternative:
    - Use TemplateView (class-based) for even less code if no logic is needed.
    """
    context = {
        "page_title": "Welcome",
        "tagline": "Your work, clearly showcased.",
    }
    return render(request, "home.html", context)