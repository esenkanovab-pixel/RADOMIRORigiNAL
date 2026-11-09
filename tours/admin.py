from django.contrib import admin
from .models import Profile, Category, Tour, Departure, Booking, Comment
from .forms import DepartureForm
admin.site.register([Profile,Category,Tour,Comment])
@admin.register(Departure)
class DepartureAdmin(admin.ModelAdmin):
    form=DepartureForm
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display=['user','departure','attended']
    readonly_fields=['user','departure','starts_at']
    def has_add_permission(self, request): return False
