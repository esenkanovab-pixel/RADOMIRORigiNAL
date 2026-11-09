from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from blog.models import Blog
from articles.models import Article
from tours.models import Tour

class IntegrationTests(TestCase):
    def test_existing_apps_and_tours_share_project(self):
        blog=Blog.objects.create(title='Старая статья',content='Содержимое')
        article=Article.objects.create(title='CRUD',content='Текст')
        tour=Tour.objects.create(title='Конный тур',description='Горы',price=1000)
        for url in [reverse('blog:list'),reverse('blog:detail',args=[blog.pk]),reverse('articles:list'),reverse('articles:detail',args=[article.pk]),reverse('home'),reverse('detail',args=[tour.pk])]:
            self.assertEqual(self.client.get(url).status_code,200)
        blog.refresh_from_db();self.assertEqual(blog.likes,1)
    def test_cross_navigation(self):
        self.assertContains(self.client.get(reverse('blog:list')),'href="/tours/"')
        self.assertContains(self.client.get(reverse('home')),'href="/blog/"')
    def test_documentation_covers_all_apps(self):
        staff=get_user_model().objects.create_superuser('docs','docs@example.com','test-password')
        self.client.force_login(staff)
        for model in ['blog.blog','articles.article','tours.booking']:
            self.assertEqual(self.client.get('/admin/doc/models/'+model+'/').status_code,200)
