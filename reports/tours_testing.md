# Отчёт о тестировании Nomad Tours

Дата: 9 ноября 2026 года. Среда: Python, Django 5.2.19, SQLite.

## Проверяемые требования

| Требование | Реализация | Ожидаемый результат |
|---|---|---|
| 1:1 | User — Profile, OneToOneField | Второй профиль одного пользователя отклоняется базой |
| 1:N | Tour — Departure, Booking — Comment | Несколько выездов маршрута и несколько комментариев покупки |
| M:N | Tour — Category, ManyToManyField | Несколько категорий у маршрута, несколько маршрутов категории |
| Один тур на дату и время | UniqueConstraint(user, starts_at) в Booking | Повтор и другой маршрут в тот же момент дают HTTP 409 |
| Разные дата или время | Независимые значения starts_at | Покупки разрешены, HTTP 302 |
| Отзывы о посещённых турах | Владелец покупки + attended + прошедшее время | Несколько отзывов разрешены; чужая покупка — 404, непосещённая — 403 |
| Отправка форм | Django ModelForm + CSRF + права | Некорректные значения не сохраняются |
| CRUD | TourForm, страницы каталога, изменения и удаления | Операции записи доступны сотрудникам |
| Документация | django.contrib.admindocs | Модели и представления доступны сотруднику в /admin/doc/ |

## Методика и результат

Запущена команда `python manage.py test tours -v 2`.
Django создаёт отдельную тестовую базу; проверки не затрагивают рабочие данные.
Тестовый клиент отправляет настоящие для Django GET/POST-запросы через URL-маршруты.
Проверяются HTTP-статусы, содержимое ответа и состояние базы после отправки.
Отдельный Client(enforce_csrf_checks=True) проверяет запрет POST без CSRF-токена.
В тестах ограничений базы используется transaction.atomic для корректного отката ошибки.

**Фактический результат: 58 тестов, OK.** Полный вывод запуска — TEST_RESULTS.txt.
Проверка `makemigrations --check --dry-run`: No changes detected.

## Реестр тестов

Каждая строка соответствует отдельному методу в tours/tests.py.
Внутри некоторых методов дополнительно проверяются несколько вариантов через subTest.

| № | Тест | Результат |
|---|---|---|
| 1 | `test_list_content_and_links` | OK |
| 2 | `test_empty_catalog` | OK |
| 3 | `test_detail_content_categories` | OK |
| 4 | `test_detail_missing` | OK |
| 5 | `test_categories_many_to_many` | OK |
| 6 | `test_departures_one_to_many` | OK |
| 7 | `test_profile_one_to_one_db` | OK |
| 8 | `test_profile_create_and_update` | OK |
| 9 | `test_profile_empty_rejected` | OK |
| 10 | `test_profile_too_long` | OK |
| 11 | `test_purchase_success` | OK |
| 12 | `test_duplicate_purchase_rejected` | OK |
| 13 | `test_different_tour_same_time_rejected` | OK |
| 14 | `test_different_time_allowed` | OK |
| 15 | `test_different_day_allowed` | OK |
| 16 | `test_different_users_same_time_allowed` | OK |
| 17 | `test_purchase_user_spoof_ignored` | OK |
| 18 | `test_purchase_past_rejected` | OK |
| 19 | `test_purchase_missing_departure` | OK |
| 20 | `test_purchase_requires_login` | OK |
| 21 | `test_purchase_get_has_no_effect` | OK |
| 22 | `test_database_prevents_conflicting_purchase` | OK |
| 23 | `test_my_bookings_private` | OK |
| 24 | `test_multiple_comments_after_visit` | OK |
| 25 | `test_comment_unconfirmed_rejected` | OK |
| 26 | `test_comment_future_even_attended_rejected` | OK |
| 27 | `test_comment_other_booking_rejected` | OK |
| 28 | `test_comment_empty_and_whitespace_rejected` | OK |
| 29 | `test_comment_too_long_rejected` | OK |
| 30 | `test_comment_max_length_allowed` | OK |
| 31 | `test_comment_requires_login` | OK |
| 32 | `test_comment_missing_booking` | OK |
| 33 | `test_comment_get_has_no_effect` | OK |
| 34 | `test_comment_booking_spoof_ignored` | OK |
| 35 | `test_comment_escaped_html` | OK |
| 36 | `test_model_comment_validation` | OK |
| 37 | `test_create_tour_staff` | OK |
| 38 | `test_create_tour_regular_user_denied` | OK |
| 39 | `test_create_invalid_fields` | OK |
| 40 | `test_update_tour_and_categories` | OK |
| 41 | `test_update_invalid_no_changes` | OK |
| 42 | `test_update_regular_user_denied` | OK |
| 43 | `test_update_missing` | OK |
| 44 | `test_delete_staff` | OK |
| 45 | `test_delete_protected_tour` | OK |
| 46 | `test_delete_regular_user_denied` | OK |
| 47 | `test_delete_get_rejected` | OK |
| 48 | `test_csrf_on_all_public_write_routes` | OK |
| 49 | `test_departure_time_change_with_bookings_rejected` | OK |
| 50 | `test_admindocs_staff_pages` | OK |
| 51 | `test_admindocs_anonymous_denied` | OK |
| 52 | `test_admin_category_submission` | OK |
| 53 | `test_admin_departure_submission` | OK |
| 54 | `test_admin_departure_invalid_data` | OK |
| 55 | `test_admin_attendance_submission` | OK |
| 56 | `test_regular_user_cannot_confirm_attendance` | OK |
| 57 | `test_login_valid_and_invalid` | OK |
| 58 | `test_logout_post` | OK |

## Что именно отправляется

- Профиль: валидный телефон, обновление, пустой и слишком длинный телефон, подмена user.
- Покупка: разрешённый выезд, повтор, другой маршрут в тот же момент, другой час/день, другой пользователь, прошедший и отсутствующий выезд; подмена user/attended/starts_at.
- Комментарий: два отзыва, пустой текст и пробелы, 2000 и 2001 символ, чужая покупка, отсутствующая покупка, неподтверждённое и будущее посещение; подмена booking и HTML-текст.
- Тур: создание и редактирование, смена категорий, пустые обязательные поля, неверная/отрицательная цена, несуществующая категория, длинный заголовок, права доступа, удаление с покупками и без них.
- Админка: создание категории, пустое/повторное название, создание выезда, повтор, ошибочная дата/время и ссылка на тур, подтверждение посещения.
- Авторизация: корректный и ошибочный пароль, выход POST. CSRF проверяется для всех форм записи публичного приложения.

## Границы проверки

Покупка в этой работе — запись бронирования, без списания денег. Проверяется совпадение точного момента старта, а не пересечение длительности маршрутов. Сотрудник подтверждает посещение вручную.
Параллельная нагрузка, платёжный шлюз и Selenium-проверки браузера не проводились. Повторная покупка дополнительно защищена ограничением базы.
Запрет переноса выезда с покупками действует через форму админки. Прямые изменения через ORM/SQL должны соблюдать это правило; DB-триггер не добавлен.

Источник по генератору документации: https://docs.djangoproject.com/en/5.2/ref/contrib/admin/admindocs/
