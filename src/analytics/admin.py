from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Count

from analytics.filters import CityFilter, CustomDateRangeFilter
from analytics.models import VisitorAnalytics, CitiesAnalytics
from analytics.services import GoogleAnalytics
from main.models import SearchDetail

import datetime


def validate_date(date_text):
    try:
        datetime.date.fromisoformat(date_text)
    except ValueError:
        raise ValidationError("Incorrect data format, should be YYYY-MM-DD")


@admin.register(VisitorAnalytics)
class ModelNameAdmin(admin.ModelAdmin):
    _unique_visitors = 1
    _website_visits = 0
    _average_time_visitor = 0
    _database_searches = 0
    _database_unique_users_search_count = 1
    _city_report = []

    list_display = [
        'website_visits', 'unique_visitors', 'average_time_visitor', 'database_searches',
        'database_searching_users', 'average_search_visitor'
    ]

    list_filter = [('range_date', CustomDateRangeFilter)]

    def get_list_display(self, request):
        start_date = request.GET.get('range_date__range__gte')
        end_date = request.GET.get('range_date__range__lte')
        if start_date:
            validate_date(start_date)
        if end_date:
            validate_date(end_date)
        self._unique_visitors, self._website_visits, self._average_time_visitor = GoogleAnalytics.visitors_report(
            start_date=start_date,
            end_date=end_date)
        self._database_searches = SearchDetail.objects.count()
        self._database_unique_users_search_count = SearchDetail.objects.values('ipaddress').annotate(Count('pk')
                                                                                                     ).count()
        return self.list_display

    def website_visits(self, obj):
        return self._website_visits

    def unique_visitors(self, obj):
        return self._unique_visitors

    def database_searches(self, obj):
        return self._database_searches

    def database_searching_users(self, obj):
        return self._database_unique_users_search_count

    def average_search_visitor(self, obj):
        if self._database_unique_users_search_count < 1:
            return 0
        return int(self._database_searches / self._database_unique_users_search_count)

    def average_time_visitor(self, obj):
        return f'{self._average_time_visitor} sec'


@admin.register(CitiesAnalytics)
class ModelNameAdmin(admin.ModelAdmin):
    _city_report = []
    list_display = ['country', 'city', 'visitors']
    list_filter = [('range_date', CustomDateRangeFilter), 'country', CityFilter]
    ordering = ['-visitors']

    def get_list_display(self, request):
        start_date = request.GET.get('range_date__range__gte')
        end_date = request.GET.get('range_date__range__lte')
        if start_date:
            validate_date(start_date)
        if end_date:
            validate_date(end_date)
        self._city_report = GoogleAnalytics.cities_report(start_date, end_date)
        CitiesAnalytics.objects.all().delete()
        CitiesAnalytics.objects.bulk_create([CitiesAnalytics(**obj) for obj in self._city_report])
        return self.list_display
