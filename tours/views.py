from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Tour, Departure, Booking, Profile, Comment
from .forms import TourForm, ProfileForm, CommentForm
staff_required = user_passes_test(lambda u: u.is_active and u.is_staff)

def index(request):
    """Каталог маршрутов. Контекст: tours. Шаблон tours/index.html."""
    return render(request, 'tours/index.html', {'tours':Tour.objects.prefetch_related('categories')})

def detail(request, pk):
    """Страница тура с выездами и отзывами подтверждённых участников."""
    tour = get_object_or_404(Tour, pk=pk)
    return render(request, 'tours/detail.html', {'tour':tour, 'departures':tour.departures.filter(starts_at__gt=timezone.now()), 'comments':Comment.objects.filter(booking__departure__tour=tour).select_related('booking__user')})

@login_required
def profile(request):
    """GET: форма профиля. POST: телефон; пользователь берётся из сессии (1:1)."""
    instance = Profile.objects.filter(user=request.user).first()
    form = ProfileForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False); obj.user = request.user; obj.save()
        return redirect('profile')
    return render(request,'tours/form.html',{'form':form,'title':'Профиль'}, status=400 if request.method=='POST' else 200)

@staff_required
def tour_create(request):
    """Создать маршрут: POST title, description, price, categories. Только сотрудники."""
    return edit_tour(request)

@staff_required
def tour_update(request, pk):
    """Изменить маршрут: валидируемая форма TourForm, только сотрудники."""
    return edit_tour(request,get_object_or_404(Tour,pk=pk))

def edit_tour(request, instance=None):
    form = TourForm(request.POST if request.method=='POST' else None,instance=instance)
    if request.method=='POST' and form.is_valid():
        tour=form.save();return redirect('detail',pk=tour.pk)
    return render(request,'tours/form.html',{'form':form,'title':'Маршрут'},status=400 if request.method=='POST' else 200)

@staff_required
@require_POST
def tour_delete(request,pk):
    """Удалить маршрут POST-запросом. Купленные выезды защищены от удаления: HTTP 409."""
    tour=get_object_or_404(Tour,pk=pk)
    try: tour.delete()
    except ProtectedError: return HttpResponse('У тура есть бронирования.',status=409)
    return redirect('home')

@login_required
@require_POST
def book(request,pk):
    """Купить/забронировать выезд. ID пользователя из сессии, ID выезда из URL.

    HTTP 302 — успех, 400 — выезд уже начался, 409 — совпадает время другой покупки.
    Оплата в учебной версии не интегрирована.
    """
    departure=get_object_or_404(Departure,pk=pk)
    if departure.starts_at <= timezone.now(): return HttpResponse('Выезд уже начался.',status=400)
    try:
        with transaction.atomic(): Booking.objects.create(user=request.user,departure=departure)
    except IntegrityError: return HttpResponse('У вас уже есть тур на эту дату и время.',status=409)
    return redirect('bookings')

@login_required
def bookings(request):
    """Личный список покупок. Чужие покупки не показываются."""
    return render(request,'tours/bookings.html',{'bookings':request.user.tour_bookings.select_related('departure__tour')})

@login_required
def comment(request,pk):
    """GET: форма отзыва. POST text: только владелец посещённой покупки.

    Чужой ID — 404. Непосещённый или будущий тур — 403. Ошибка формы — 400.
    Несколько комментариев одного участника разрешены.
    """
    booking=get_object_or_404(Booking,pk=pk,user=request.user)
    if not booking.attended or booking.starts_at > timezone.now(): return HttpResponse('Сначала посетите тур.',status=403)
    instance=Comment(booking=booking)
    form=CommentForm(request.POST if request.method=='POST' else None,instance=instance)
    if request.method=='POST' and form.is_valid():
        form.save();return redirect('detail',pk=booking.departure.tour_id)
    return render(request,'tours/form.html',{'form':form,'title':'Отзыв'},status=400 if request.method=='POST' else 200)

def documentation(request):
    """Учебная документация: бизнес-правила, связи, формы и запуск тестов."""
    return render(request,'tours/docs.html')
