from django.db.models import F
from django.views.generic import DetailView, ListView
from .models import Blog

class BlogListView(ListView):
    model = Blog
    template_name = "blog/blog_list.html"
    context_object_name = "blogs"

class BlogDetailView(DetailView):
    model = Blog
    template_name = "blog/blog_detail.html"
    context_object_name = "blog"

    def get_object(self, queryset=None):
        blog = super().get_object(queryset)
        if self.request.method == "GET":
            Blog.objects.filter(pk=blog.pk).update(likes=F("likes") + 1)
            blog.refresh_from_db(fields=["likes"])
        return blog
