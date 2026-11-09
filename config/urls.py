from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from tours import views as tours_views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="blog:list", permanent=False)),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("blog/", include("blog.urls")),
    path("articles/", include("articles.urls")),
    path('accounts/', include('django.contrib.auth.urls')),
    path('tours/', tours_views.index, name='home'),
    path('docs/', tours_views.documentation, name='docs'),
    path('profile/', tours_views.profile, name='profile'),
    path('tours/new/', tours_views.tour_create, name='tour-create'),
    path('tours/<int:pk>/', tours_views.detail, name='detail'),
    path('tours/<int:pk>/edit/', tours_views.tour_update, name='tour-update'),
    path('tours/<int:pk>/delete/', tours_views.tour_delete, name='tour-delete'),
    path('departures/<int:pk>/book/', tours_views.book, name='book'),
    path('bookings/', tours_views.bookings, name='bookings'),
    path('bookings/<int:pk>/comment/', tours_views.comment, name='comment'),
]
