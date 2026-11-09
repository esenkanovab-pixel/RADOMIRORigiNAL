from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)
from .forms import ArticleForm
from .models import Article


class ArticleListView(ListView):
    model = Article
    context_object_name = "articles"
    template_name = "articles/article_list.html"


class ArticleDetailView(DetailView):
    model = Article
    context_object_name = "article"
    template_name = "articles/article_detail.html"


class ArticleCreateView(CreateView):
    model = Article
    form_class = ArticleForm
    template_name = "articles/article_form.html"
    extra_context = {"page_title": "Создание статьи"}


class ArticleUpdateView(UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = "articles/article_form.html"
    extra_context = {"page_title": "Редактирование статьи"}


class ArticleDeleteView(DeleteView):
    model = Article
    template_name = "articles/article_confirm_delete.html"
    success_url = reverse_lazy("articles:list")
