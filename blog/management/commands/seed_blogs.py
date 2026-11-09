from django.core.management.base import BaseCommand
from blog.models import Blog

class Command(BaseCommand):
    help = "Добавляет три демонстрационные статьи, не изменяя существующие."

    def handle(self, *args, **options):
        examples = [
            ("Что такое Django", "Django — фреймворк для создания веб-приложений на Python.\n\nВ этом проекте ListView показывает список статей, а DetailView открывает одну статью по её идентификатору."),
            ("Как работают тесты", "Тестовый клиент Django отправляет запросы без запуска сервера. TestCase создаёт отдельную тестовую базу данных.\n\nТесты проверяют статус ответа, шаблон, содержимое и изменения в базе."),
            ("Счётчик просмотров", "Поле likes имеет значение по умолчанию 0. Каждый GET-запрос к детальной странице увеличивает его на 1.\n\nВыражение F позволяет увеличить значение непосредственно в базе данных."),
        ]
        created = 0
        for title, content in examples:
            _, is_new = Blog.objects.get_or_create(title=title, defaults={"content": content})
            created += int(is_new)
        self.stdout.write(self.style.SUCCESS(f"Добавлено статей: {created}"))
