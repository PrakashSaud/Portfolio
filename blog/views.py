from blog.models import BlogPost
from django.shortcuts import render
from django.views.generic import DetailView, ListView


# Create your views here.
class BlogPostDetailView(DetailView):
    model = BlogPost
    # template_name = 'blog/blogpost_detail.html'
    # context_object_name = 'blogpost'
