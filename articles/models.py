from django.db import models
from django.urls import reverse


class Article(models.Model):
    """Статья отдельного приложения CRUD: создание, чтение, изменение и удаление."""
    title = models.CharField("Заголовок", max_length=200)
    content = models.TextField("Содержание")

    class Meta:
        ordering = ["-pk"]
        verbose_name = "CRUD-статья"
        verbose_name_plural = "CRUD-статьи"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("articles:detail", kwargs={"pk": self.pk})
