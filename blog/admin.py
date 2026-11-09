from django.contrib import admin
from .models import Blog

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "likes")
    search_fields = ("title", "content")
    readonly_fields = ("likes",)
