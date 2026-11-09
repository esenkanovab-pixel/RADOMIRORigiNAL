from django.test import TestCase
from django.urls import reverse
from .models import Blog

class BlogTests(TestCase):
    def setUp(self):
        self.blog = Blog.objects.create(
            title="Первая статья",
            content="Короткое содержание первой статьи",
        )
        self.list_url = reverse("blog:list")
        self.detail_url = reverse("blog:detail", kwargs={"pk": self.blog.pk})

    def test_list_returns_200(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/blog_list.html")

    def test_list_contains_blog_and_id(self):
        response = self.client.get(self.list_url)
        self.assertIn(self.blog, response.context["blogs"])
        self.assertEqual(response.context["blogs"][0].pk, self.blog.pk)

    def test_list_displays_content(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, self.blog.title)
        self.assertContains(response, self.blog.content)

    def test_empty_list(self):
        Blog.objects.all().delete()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["blogs"]), 0)
        self.assertContains(response, "Статей пока нет")

    def test_detail_link_works(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, f'href="{self.detail_url}"')
        detail = self.client.get(self.detail_url)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.context["blog"].pk, self.blog.pk)

    def test_detail_returns_correct_blog(self):
        response = self.client.get(self.detail_url)
        self.assertTemplateUsed(response, "blog/blog_detail.html")
        self.assertEqual(response.context["blog"].pk, self.blog.pk)
        self.assertContains(response, self.blog.title)
        self.assertContains(response, self.blog.content)

    def test_missing_id_returns_404(self):
        url = reverse("blog:detail", kwargs={"pk": self.blog.pk + 1000})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_new_blog_likes_default_zero(self):
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.likes, 0)

    def test_detail_increments_likes(self):
        other = Blog.objects.create(title="Другая статья", content="Текст")
        response = self.client.get(self.detail_url)
        self.blog.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.blog.likes, 1)
        self.assertEqual(other.likes, 0)
        self.assertEqual(response.context["blog"].likes, 1)

    def test_list_does_not_increment_likes(self):
        self.client.get(self.list_url)
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.likes, 0)

    def test_two_get_requests_increment_twice(self):
        self.client.get(self.detail_url)
        self.client.get(self.detail_url)
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.likes, 2)

    def test_head_does_not_increment_likes(self):
        response = self.client.head(self.detail_url)
        self.blog.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.blog.likes, 0)
