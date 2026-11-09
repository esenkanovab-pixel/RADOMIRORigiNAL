from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Profile, Category, Tour, Departure, Booking, Comment
from .forms import DepartureForm

class TourTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User=get_user_model()
        cls.user=User.objects.create_user('tourist',password='test-pass-123')
        cls.other=User.objects.create_user('other',password='test-pass-123')
        cls.staff=User.objects.create_superuser('staff','staff@example.com','test-pass-123')
        cls.horse=Category.objects.create(name='Конный')
        cls.walk=Category.objects.create(name='Пеший')
        cls.tour=Tour.objects.create(title='Конный тур',description='Горный маршрут',price=2500)
        cls.tour.categories.add(cls.horse)
        cls.second=Tour.objects.create(title='Поход',description='Пешком в горы',price=1500)
        cls.second.categories.add(cls.walk)
        cls.when=timezone.now()+timedelta(days=5)
        cls.departure=Departure.objects.create(tour=cls.tour,starts_at=cls.when)
        cls.same_time=Departure.objects.create(tour=cls.second,starts_at=cls.when)
        cls.later=Departure.objects.create(tour=cls.tour,starts_at=cls.when+timedelta(hours=1))
        cls.next_day=Departure.objects.create(tour=cls.tour,starts_at=cls.when+timedelta(days=1))
        cls.past=Departure.objects.create(tour=cls.tour,starts_at=timezone.now()-timedelta(days=2))
    def setUp(self): self.client.force_login(self.user)
    def purchase(self,dep=None,**data): return self.client.post(reverse('book',args=[(dep or self.departure).pk]),data)
    def visited(self,user=None,attended=True,dep=None):
        return Booking.objects.create(user=user or self.user,departure=dep or self.past,attended=attended)
    def post_comment(self,booking,text='Отличный тур!',**extra):
        return self.client.post(reverse('comment',args=[booking.pk]),{'text':text,**extra})
    def payload(self,**extra):
        return {'title':'Новый маршрут','description':'Описание тура','price':'1000.00','categories':[self.horse.pk,self.walk.pk],**extra}

    def test_list_content_and_links(self):
        response=self.client.get(reverse('home'))
        self.assertContains(response,self.tour.title)
        self.assertContains(response,reverse('detail',args=[self.tour.pk]))
    def test_empty_catalog(self):
        Tour.objects.all().delete()
        self.assertContains(self.client.get(reverse('home')),'Туры пока не добавлены')
    def test_detail_content_categories(self):
        response=self.client.get(reverse('detail',args=[self.tour.pk]))
        self.assertContains(response,self.tour.description)
        self.assertContains(response,'2500')
    def test_detail_missing(self): self.assertEqual(self.client.get('/tours/99999/').status_code,404)
    def test_categories_many_to_many(self):
        self.tour.categories.add(self.walk)
        self.assertEqual(self.tour.categories.count(),2)
        self.assertEqual(self.walk.tours.count(),2)
    def test_departures_one_to_many(self): self.assertGreater(self.tour.departures.count(),1)
    def test_profile_one_to_one_db(self):
        Profile.objects.create(user=self.user,phone='123')
        with self.assertRaises(IntegrityError),transaction.atomic(): Profile.objects.create(user=self.user,phone='456')
    def test_profile_create_and_update(self):
        for phone in ['+996555123456','+996700123456']:
            self.assertEqual(self.client.post('/profile/',{'phone':phone,'user':self.other.pk}).status_code,302)
        self.assertEqual(Profile.objects.get(user=self.user).phone,'+996700123456')
        self.assertFalse(Profile.objects.filter(user=self.other).exists())
        self.assertEqual(Profile.objects.count(),1)
    def test_profile_empty_rejected(self):
        self.assertEqual(self.client.post('/profile/',{'phone':''}).status_code,400)
        self.assertFalse(Profile.objects.exists())
    def test_profile_too_long(self): self.assertEqual(self.client.post('/profile/',{'phone':'x'*31}).status_code,400)
    def test_purchase_success(self):
        self.assertEqual(self.purchase().status_code,302)
        obj=Booking.objects.get()
        self.assertEqual(obj.user,self.user)
        self.assertEqual(obj.starts_at,self.departure.starts_at)
        self.assertFalse(obj.attended)
    def test_duplicate_purchase_rejected(self):
        self.purchase()
        self.assertEqual(self.purchase().status_code,409)
        self.assertEqual(Booking.objects.count(),1)
    def test_different_tour_same_time_rejected(self):
        self.purchase()
        self.assertEqual(self.purchase(self.same_time).status_code,409)
        self.assertEqual(Booking.objects.count(),1)
    def test_different_time_allowed(self):
        self.purchase()
        self.assertEqual(self.purchase(self.later).status_code,302)
        self.assertEqual(Booking.objects.count(),2)
    def test_different_day_allowed(self):
        self.purchase()
        self.assertEqual(self.purchase(self.next_day).status_code,302)
    def test_different_users_same_time_allowed(self):
        self.purchase();self.client.force_login(self.other)
        self.assertEqual(self.purchase().status_code,302)
        self.assertEqual(Booking.objects.count(),2)
    def test_purchase_user_spoof_ignored(self):
        self.purchase(user=self.other.pk,attended=True,starts_at='2000-01-01')
        obj=Booking.objects.get()
        self.assertEqual(obj.user,self.user);self.assertFalse(obj.attended)
        self.assertEqual(obj.starts_at,self.when)
    def test_purchase_past_rejected(self):
        self.assertEqual(self.purchase(self.past).status_code,400)
        self.assertFalse(Booking.objects.exists())
    def test_purchase_missing_departure(self): self.assertEqual(self.client.post('/departures/99999/book/').status_code,404)
    def test_purchase_requires_login(self):
        self.client.logout();self.assertEqual(self.purchase().status_code,302)
        self.assertFalse(Booking.objects.exists())
    def test_purchase_get_has_no_effect(self):
        self.assertEqual(self.client.get(reverse('book',args=[self.departure.pk])).status_code,405)
        self.assertFalse(Booking.objects.exists())
    def test_database_prevents_conflicting_purchase(self):
        self.purchase()
        with self.assertRaises(IntegrityError),transaction.atomic(): Booking.objects.create(user=self.user,departure=self.same_time)
    def test_my_bookings_private(self):
        self.visited(user=self.other)
        response=self.client.get('/bookings/')
        self.assertEqual(list(response.context['bookings']),[])
    def test_multiple_comments_after_visit(self):
        booking=self.visited()
        for text in ['Очень понравилось','Спасибо гиду!']:
            self.assertEqual(self.post_comment(booking,text).status_code,302)
        self.assertEqual(booking.comments.count(),2)
        self.assertContains(self.client.get(reverse('detail',args=[self.tour.pk])),'Спасибо гиду!')
    def test_comment_unconfirmed_rejected(self):
        self.assertEqual(self.post_comment(self.visited(attended=False)).status_code,403)
        self.assertFalse(Comment.objects.exists())
    def test_comment_future_even_attended_rejected(self):
        self.assertEqual(self.post_comment(self.visited(dep=self.departure)).status_code,403)
    def test_comment_other_booking_rejected(self):
        self.assertEqual(self.post_comment(self.visited(user=self.other)).status_code,404)
        self.assertFalse(Comment.objects.exists())
    def test_comment_empty_and_whitespace_rejected(self):
        booking=self.visited()
        for text in ['', '   ']: self.assertEqual(self.post_comment(booking,text).status_code,400)
        self.assertFalse(Comment.objects.exists())
    def test_comment_too_long_rejected(self):
        self.assertEqual(self.post_comment(self.visited(),'x'*2001).status_code,400)
    def test_comment_max_length_allowed(self): self.assertEqual(self.post_comment(self.visited(),'x'*2000).status_code,302)
    def test_comment_requires_login(self):
        booking=self.visited();self.client.logout()
        self.assertEqual(self.post_comment(booking).status_code,302)
        self.assertFalse(Comment.objects.exists())
    def test_comment_missing_booking(self): self.assertEqual(self.client.post('/bookings/99999/comment/',{'text':'Текст'}).status_code,404)
    def test_comment_get_has_no_effect(self):
        booking=self.visited()
        self.assertEqual(self.client.get(reverse('comment',args=[booking.pk])).status_code,200)
        self.assertFalse(Comment.objects.exists())
    def test_comment_booking_spoof_ignored(self):
        mine=self.visited();other=self.visited(user=self.other)
        response=self.client.post(reverse('comment',args=[mine.pk]),{'text':'Мой отзыв','booking':other.pk})
        self.assertEqual(response.status_code,302)
        self.assertEqual(Comment.objects.get().booking,mine)
    def test_comment_escaped_html(self):
        self.post_comment(self.visited(),'<script>alert(1)</script>')
        response=self.client.get(reverse('detail',args=[self.tour.pk]))
        self.assertNotContains(response,'<script>alert(1)</script>')
        self.assertContains(response,'&lt;script&gt;')
    def test_model_comment_validation(self):
        comment=Comment(booking=self.visited(attended=False),text='Текст')
        with self.assertRaises(ValidationError): comment.full_clean()
    def test_create_tour_staff(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post('/tours/new/',self.payload()).status_code,302)
        self.assertEqual(Tour.objects.get(title='Новый маршрут').categories.count(),2)
    def test_create_tour_regular_user_denied(self):
        before=Tour.objects.count()
        self.assertEqual(self.client.post('/tours/new/',self.payload()).status_code,302)
        self.assertEqual(Tour.objects.count(),before)
    def test_create_invalid_fields(self):
        self.client.force_login(self.staff);before=Tour.objects.count()
        for patch in [{'title':''},{'description':''},{'price':'-1'},{'price':'abc'},{'categories':[]},{'categories':[99999]},{'title':'x'*151}]:
            with self.subTest(patch=patch): self.assertEqual(self.client.post('/tours/new/',self.payload(**patch)).status_code,400)
        self.assertEqual(Tour.objects.count(),before)
    def test_update_tour_and_categories(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(reverse('tour-update',args=[self.tour.pk]),self.payload(categories=[self.walk.pk])).status_code,302)
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.title,'Новый маршрут');self.assertEqual(self.tour.price,Decimal('1000'))
        self.assertEqual(list(self.tour.categories.all()),[self.walk])
    def test_update_invalid_no_changes(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(reverse('tour-update',args=[self.tour.pk]),self.payload(price='-3')).status_code,400)
        self.tour.refresh_from_db();self.assertEqual(self.tour.price,2500)
    def test_update_regular_user_denied(self):
        self.client.post(reverse('tour-update',args=[self.tour.pk]),self.payload())
        self.tour.refresh_from_db();self.assertEqual(self.tour.title,'Конный тур')
    def test_update_missing(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post('/tours/99999/edit/',self.payload()).status_code,404)
    def test_delete_staff(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(reverse('tour-delete',args=[self.second.pk])).status_code,302)
        self.assertFalse(Tour.objects.filter(pk=self.second.pk).exists())
    def test_delete_protected_tour(self):
        self.purchase();self.client.force_login(self.staff)
        self.assertEqual(self.client.post(reverse('tour-delete',args=[self.tour.pk])).status_code,409)
        self.assertTrue(Tour.objects.filter(pk=self.tour.pk).exists())
    def test_delete_regular_user_denied(self):
        self.client.post(reverse('tour-delete',args=[self.tour.pk]))
        self.assertTrue(Tour.objects.filter(pk=self.tour.pk).exists())
    def test_delete_get_rejected(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('tour-delete',args=[self.tour.pk])).status_code,405)
    def test_csrf_on_all_public_write_routes(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.staff)
        booking=self.visited()
        urls=['/profile/','/tours/new/',reverse('tour-update',args=[self.tour.pk]),reverse('tour-delete',args=[self.tour.pk]),reverse('book',args=[self.departure.pk]),reverse('comment',args=[booking.pk])]
        for url in urls:
            with self.subTest(url=url): self.assertEqual(client.post(url,{}).status_code,403)
    def test_departure_time_change_with_bookings_rejected(self):
        self.purchase()
        form=DepartureForm(data={'tour':self.tour.pk,'starts_at':self.when+timedelta(hours=3)},instance=self.departure)
        self.assertFalse(form.is_valid())
    def test_admindocs_staff_pages(self):
        self.client.force_login(self.staff)
        for url in ['/admin/doc/','/admin/doc/models/','/admin/doc/models/tours.booking/','/admin/doc/views/','/docs/']:
            with self.subTest(url=url): self.assertEqual(self.client.get(url).status_code,200)
    def test_admindocs_anonymous_denied(self):
        self.client.logout();self.assertEqual(self.client.get('/admin/doc/').status_code,302)

    def test_admin_category_submission(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post('/admin/tours/category/add/',{'name':'Мото','_save':'Сохранить'}).status_code,302)
        self.assertTrue(Category.objects.filter(name='Мото').exists())
        for name in ['', 'Конный']:
            response=self.client.post('/admin/tours/category/add/',{'name':name,'_save':'Сохранить'})
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.context['adminform'].form.errors)
        self.assertEqual(Category.objects.filter(name='Конный').count(),1)
    def test_admin_departure_submission(self):
        self.client.force_login(self.staff)
        data={'tour':self.tour.pk,'starts_at_0':'2030-05-20','starts_at_1':'10:00:00','_save':'Сохранить'}
        self.assertEqual(self.client.post('/admin/tours/departure/add/',data).status_code,302)
        response=self.client.post('/admin/tours/departure/add/',data)
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.context['adminform'].form.errors)
    def test_admin_departure_invalid_data(self):
        self.client.force_login(self.staff)
        for patch in [{'tour':99999},{'starts_at_0':'wrong'},{'starts_at_1':'99:99'}]:
            data={'tour':self.tour.pk,'starts_at_0':'2030-05-20','starts_at_1':'10:00:00',**patch}
            response=self.client.post('/admin/tours/departure/add/',data)
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.context['adminform'].form.errors)
    def test_admin_attendance_submission(self):
        booking=self.visited(attended=False);self.client.force_login(self.staff)
        url=f'/admin/tours/booking/{booking.pk}/change/'
        self.assertEqual(self.client.post(url,{'attended':'on','_save':'Сохранить'}).status_code,302)
        booking.refresh_from_db();self.assertTrue(booking.attended)
    def test_regular_user_cannot_confirm_attendance(self):
        booking=self.visited(attended=False)
        self.assertEqual(self.client.post(f'/admin/tours/booking/{booking.pk}/change/',{'attended':'on'}).status_code,302)
        booking.refresh_from_db();self.assertFalse(booking.attended)
    def test_login_valid_and_invalid(self):
        self.client.logout()
        self.assertEqual(self.client.post('/accounts/login/',{'username':'tourist','password':'incorrect'}).status_code,200)
        self.assertNotIn('_auth_user_id',self.client.session)
        self.assertEqual(self.client.post('/accounts/login/',{'username':'tourist','password':'test-pass-123'}).status_code,302)
        self.assertEqual(int(self.client.session['_auth_user_id']),self.user.pk)
    def test_logout_post(self):
        self.assertEqual(self.client.post('/accounts/logout/').status_code,302)
        self.assertNotIn('_auth_user_id',self.client.session)
