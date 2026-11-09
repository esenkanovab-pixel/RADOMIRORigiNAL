from django.urls import path
from .views import (
    ArticleCreateView, ArticleDeleteView, ArticleDetailView,
    ArticleListView, ArticleUpdateView,
)

app_name = "articles"
urlpatterns = [
    path("", ArticleListView.as_view(), name="list"),
    path("create/", ArticleCreateView.as_view(), name="create"),
    path("<int:pk>/", ArticleDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", ArticleUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", ArticleDeleteView.as_view(), name="delete"),
]
