from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tours.models import Tour, Category, Departure
class Command(BaseCommand):
    help='Создать категории и демонстрационные туры без паролей'
    def handle(self,*args,**kwargs):
        cats=[Category.objects.get_or_create(name=n)[0] for n in ['Конный','Пеший','Мото']]
        for title,category,price in [('Конная прогулка в Чон-Кемине',cats[0],2500),('Поход в Ала-Арче',cats[1],1500),('Мототур по горным дорогам',cats[2],4500)]:
            tour,_=Tour.objects.get_or_create(title=title,defaults={'description':'Маршрут с гидом. Подробности уточняются перед поездкой.','price':price})
            tour.categories.add(category)
            if not tour.departures.exists(): Departure.objects.create(tour=tour,starts_at=(timezone.now()+timedelta(days=7)).replace(hour=9,minute=0,second=0,microsecond=0))
        self.stdout.write(self.style.SUCCESS('Демонстрационные туры готовы.'))
