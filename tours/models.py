from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

class Profile(models.Model):
    """Профиль туриста. Связь 1:1 с auth.User: один пользователь — один профиль."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tour_profile', help_text='Один профиль на пользователя')
    phone = models.CharField(max_length=30, help_text='Контактный телефон туриста')
    def __str__(self): return str(self.user)

class Category(models.Model):
    """Вид путешествия: конный, пеший, мото. Один вид относится к многим турам."""
    name = models.CharField(max_length=80, unique=True)
    def __str__(self): return self.name

class Tour(models.Model):
    """Маршрут Nomad Tours. Категории связаны M:N: у тура может быть несколько видов."""
    title = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    categories = models.ManyToManyField(Category, related_name='tours', help_text='Конный, пеший, мото или смешанный маршрут')
    def __str__(self): return self.title

class Departure(models.Model):
    """Выезд тура в конкретный момент. Tour → Departure: связь 1:N."""
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='departures')
    starts_at = models.DateTimeField(help_text='Дата и время старта в часовом поясе сайта')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['tour','starts_at'], name='unique_tour_departure')]
    def __str__(self): return f'{self.tour}: {timezone.localtime(self.starts_at):%d.%m.%Y %H:%M}'

class Booking(models.Model):
    """Покупка/бронь без платёжного шлюза. Один пользователь — один тур на момент старта.

    starts_at копируется из выезда при создании. База защищает уникальность user + starts_at
    даже при параллельных запросах. Дату выезда с бронированиями менять нельзя.
    attended устанавливается сотрудником после фактического посещения.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tour_bookings')
    departure = models.ForeignKey(Departure, on_delete=models.PROTECT, related_name='bookings')
    starts_at = models.DateTimeField(editable=False)
    attended = models.BooleanField(default=False, help_text='Подтверждается сотрудником после посещения')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','starts_at'], name='one_tour_per_user_time')]
    def save(self, *args, **kwargs):
        self.starts_at = self.departure.starts_at
        super().save(*args, **kwargs)
    def __str__(self): return f'{self.user} — {self.departure}'

class Comment(models.Model):
    """Отзыв о посещённом туре. Booking → Comment: 1:N, число отзывов не ограничено."""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    def clean(self):
        super().clean()
        if self.booking_id and (not self.booking.attended or self.booking.starts_at > timezone.now()):
            raise ValidationError('Комментарий разрешён только после подтверждённого посещения тура.')
    def __str__(self): return self.text[:60]
