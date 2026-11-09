from django.urls import include, path
from django.views.generic import DetailView
from blog.models import Blog
from blog.views import BlogListView

class BlogDetailBeforeImplementation(DetailView):
    model = Blog
    template_name = "blog/blog_detail.html"
    context_object_name = "blog"

patterns = [
    path("", BlogListView.as_view(), name="list"),
    path("<int:pk>/", BlogDetailBeforeImplementation.as_view(), name="detail"),
]
urlpatterns = [path("blog/", include((patterns, "blog"), namespace="blog"))]
