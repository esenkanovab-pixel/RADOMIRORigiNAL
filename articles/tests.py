from django.test import Client, TestCase
from django.urls import reverse
from .models import Article


class ArticleCRUDTests(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title="Первая CRUD-статья", content="Первоначальный текст"
        )
        self.list_url = reverse("articles:list")
        self.create_url = reverse("articles:create")
        self.detail_url = self.article.get_absolute_url()
        self.update_url = reverse(
            "articles:update", kwargs={"pk": self.article.pk}
        )
        self.delete_url = reverse(
            "articles:delete", kwargs={"pk": self.article.pk}
        )

    def test_list_displays_article_and_actions(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "articles/article_list.html")
        self.assertContains(response, self.article.title)
        for url in [self.create_url, self.detail_url,
                    self.update_url, self.delete_url]:
            self.assertContains(response, f'href="{url}"')

    def test_empty_list(self):
        Article.objects.all().delete()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Статей пока нет")

    def test_detail_displays_saved_data(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "articles/article_detail.html")
        self.assertEqual(response.context["article"].pk, self.article.pk)
        self.assertContains(response, self.article.title)
        self.assertContains(response, self.article.content)

    def test_create_get_displays_form(self):
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "articles/article_form.html")
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="content"')

    def test_create_post_saves_article(self):
        response = self.client.post(
            self.create_url,
            {"title": "Новая статья", "content": "Новый текст"},
        )
        created = Article.objects.get(title="Новая статья")
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(created.content, "Новый текст")
        self.assertRedirects(response, created.get_absolute_url())

    def test_invalid_create_does_not_save(self):
        response = self.client.post(
            self.create_url, {"title": "", "content": "Текст"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", response.context["form"].errors)
        self.assertEqual(Article.objects.count(), 1)

    def test_update_get_has_initial_data(self):
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.instance.pk, self.article.pk)
        self.assertEqual(form.initial["title"], self.article.title)

    def test_update_post_changes_only_selected_article(self):
        other = Article.objects.create(title="Другая", content="Без изменений")
        response = self.client.post(
            self.update_url,
            {"title": "Изменённая", "content": "Изменённый текст"},
        )
        self.article.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(self.article.title, "Изменённая")
        self.assertEqual(self.article.content, "Изменённый текст")
        self.assertEqual(other.title, "Другая")
        self.assertEqual(other.content, "Без изменений")
        self.assertRedirects(response, self.detail_url)

    def test_invalid_update_preserves_data(self):
        response = self.client.post(
            self.update_url, {"title": "Изменение", "content": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("content", response.context["form"].errors)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Первая CRUD-статья")
        self.assertEqual(self.article.content, "Первоначальный текст")

    def test_delete_get_only_asks_confirmation(self):
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "articles/article_confirm_delete.html"
        )
        self.assertTrue(Article.objects.filter(pk=self.article.pk).exists())

    def test_delete_post_removes_only_selected_article(self):
        other = Article.objects.create(title="Другая", content="Сохранить")
        response = self.client.post(self.delete_url)
        self.assertFalse(Article.objects.filter(pk=self.article.pk).exists())
        self.assertTrue(Article.objects.filter(pk=other.pk).exists())
        self.assertRedirects(response, self.list_url)

    def test_missing_detail_update_delete_return_404(self):
        for name in ["detail", "update", "delete"]:
            url = reverse("articles:" + name, kwargs={"pk": 999999})
            with self.subTest(route=name, method="GET"):
                self.assertEqual(self.client.get(url).status_code, 404)
            if name != "detail":
                with self.subTest(route=name, method="POST"):
                    response = self.client.post(
                        url, {"title": "Текст", "content": "Текст"}
                    )
                    self.assertEqual(response.status_code, 404)

    def test_post_without_csrf_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            self.create_url, {"title": "Запрет", "content": "Текст"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Article.objects.count(), 1)

    def test_post_with_csrf_is_accepted(self):
        client = Client(enforce_csrf_checks=True)
        client.get(self.create_url)
        token = client.cookies["csrftoken"].value
        response = client.post(
            self.create_url,
            {"title": "Разрешено", "content": "Текст",
             "csrfmiddlewaretoken": token},
        )
        created = Article.objects.get(title="Разрешено")
        self.assertRedirects(response, created.get_absolute_url())
