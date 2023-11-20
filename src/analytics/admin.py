import datetime
from django.contrib import admin
from django.db.models import Count
from django.utils.timezone import now

from analytics.models import VisitorAnalytics, CitiesAnalytics, PagesAnalytics, DeviceAnalytics, ChannelAnalytics
from analytics.filters import CityFilter, CustomDateRangeFilter, ModelDeviceFilter, CustomDateFilter
from analytics.services import GoogleAnalytics
from django.core.exceptions import ValidationError

from main.models import SearchDetail


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

    list_display = [
        'website_visits', 'unique_visitors', 'average_time_visitor', 'database_searches',
        'database_searching_users', 'average_search_visitor'
    ]

    list_filter = [('range_date', CustomDateRangeFilter), CustomDateFilter]

    def get_list_display(self, request):
        start_date = request.GET.get('range_date__range__gte')
        end_date = request.GET.get('range_date__range__lte')
        custom_date = request.GET.get('date')
        if custom_date and custom_date in ['1', '2', '3', '4']:
            now_date = now().date()
            if custom_date == '1':
                start_date = str(now_date)
                end_date = str(now_date + datetime.timedelta(days=1))
            elif custom_date == '2':
                start_date = str(now_date - datetime.timedelta(days=7))
                end_date = str(now_date + datetime.timedelta(days=1))
            elif custom_date == '3':
                start_date = str(now_date.replace(day=1))
                now_date_month = now_date.month
                next_month = now_date.month + 1 if now_date_month < 12 else 1
                end_date = str(now_date.replace(day=1, month=next_month))
            else:
                start_date = str(now_date.replace(month=1, day=1))
                end_date = str(now_date.replace(year=now_date.year + 1, month=1, day=1))
        else:
            if start_date:
                validate_date(start_date)
            if end_date:
                validate_date(end_date)
        self._unique_visitors, self._website_visits, self._average_time_visitor = GoogleAnalytics.visitors_report(
            start_date=start_date,
            end_date=end_date)

        search_database_query = {}
        if start_date:
            search_database_query['date_created__gte'] = start_date
        if end_date:
            search_database_query['date_created__lte'] = end_date
        self._database_searches = SearchDetail.objects.filter(**search_database_query).count()
        self._database_unique_users_search_count = SearchDetail.objects.filter(**search_database_query
                                                                               ).values('ipaddress'
                                                                                        ).annotate(Count('pk')).count()
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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CitiesAnalytics)
class ModelNameAdmin(admin.ModelAdmin):
    _city_report = []
    list_display = ['country', 'city', 'visitors']
    list_filter = [('range_date', CustomDateRangeFilter), CustomDateFilter, 'country', CityFilter]
    ordering = ['-visitors']

    def get_list_display(self, request):
        start_date = request.GET.get('range_date__range__gte')
        end_date = request.GET.get('range_date__range__lte')
        custom_date = request.GET.get('date')
        if custom_date and custom_date in ['1', '2', '3', '4']:
            now_date = now().date()
            if custom_date == '1':
                start_date = str(now_date)
                end_date = str(now_date + datetime.timedelta(days=1))
            elif custom_date == '2':
                start_date = str(now_date - datetime.timedelta(days=7))
                end_date = str(now_date + datetime.timedelta(days=1))
            elif custom_date == '3':
                start_date = str(now_date.replace(day=1))
                now_date_month = now_date.month
                next_month = now_date.month + 1 if now_date_month < 12 else 1
                end_date = str(now_date.replace(day=1, month=next_month))
            else:
                start_date = str(now_date.replace(month=1, day=1))
                end_date = str(now_date.replace(year=now_date.year + 1, month=1, day=1))
        else:
            if start_date:
                validate_date(start_date)
            if end_date:
                validate_date(end_date)
        self._city_report = GoogleAnalytics.cities_report(start_date, end_date)
        CitiesAnalytics.objects.all().delete()
        CitiesAnalytics.objects.bulk_create([CitiesAnalytics(**obj) for obj in self._city_report])
        return self.list_display

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PagesAnalytics)
class ModelNameAdmin(admin.ModelAdmin):
    _page_report = []
    list_display = ['page_path', 'visitors', 'get_avg_engagement_time']
    list_filter = [('range_date', CustomDateRangeFilter), CustomDateFilter]
    ordering = ['-visitors']

    def get_avg_engagement_time(self, obj):
        return f'{obj.avg_engagement_time} sec'

    def get_list_display(self, request):
        start_date = request.GET.get('range_date__range__gte')
        end_date = request.GET.get('range_date__range__lte')
        custom_date = request.GET.get('date')
        if custom_date and custom_date in ['1', '2', '3', '4']:
            now_date = now().date()
            if custom_date == '1':
                start_date = str(now_date)
                end_date = str(now_date + datetime.timedelta(days=1))
            elif custom_date == '2':
                start_date = str(now_date - datetime.timedelta(days=7))
                end_date = str(now_date + datetime.timedelta(days=1))
            elif custom_date == '3':
                start_date = str(now_date.replace(day=1))
                now_date_month = now_date.month
                next_month = now_date.month + 1 if now_date_month < 12 else 1
                end_date = str(now_date.replace(day=1, month=next_month))
            else:
                start_date = str(now_date.replace(month=1, day=1))
                end_date = str(now_date.replace(year=now_date.year + 1, month=1, day=1))
        else:
            if start_date:
                validate_date(start_date)
            if end_date:
                validate_date(end_date)
        self._page_report = GoogleAnalytics.pages_report(start_date, end_date)
        PagesAnalytics.objects.all().delete()
        PagesAnalytics.objects.bulk_create([PagesAnalytics(**obj) for obj in self._page_report])
        return self.list_display

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DeviceAnalytics)
class ModelNameAdmin(admin.ModelAdmin):
    _device_report = []
    list_display = ['category', 'model', 'visitors']
    list_filter = [('range_date', CustomDateRangeFilter), CustomDateFilter, 'category', ModelDeviceFilter]
    ordering = ['-visitors']

    def get_list_display(self, request):
        start_date = request.GET.get('range_date__range__gte')
        end_date = request.GET.get('range_date__range__lte')
        custom_date = request.GET.get('date')
        if custom_date and custom_date in ['1', '2', '3', '4']:
            now_date = now().date()
            if custom_date == '1':
                start_date = str(now_date)
                end_date = str(now_date + datetime.timedelta(days=1))
            elif custom_date == '2':
                start_date = str(now_date - datetime.timedelta(days=7))
                end_date = str(now_date + datetime.timedelta(days=1))
            elif custom_date == '3':
                start_date = str(now_date.replace(day=1))
                now_date_month = now_date.month
                next_month = now_date.month + 1 if now_date_month < 12 else 1
                end_date = str(now_date.replace(day=1, month=next_month))
            else:
                start_date = str(now_date.replace(month=1, day=1))
                end_date = str(now_date.replace(year=now_date.year + 1, month=1, day=1))
        else:
            if start_date:
                validate_date(start_date)
            if end_date:
                validate_date(end_date)
        self._device_report = GoogleAnalytics.device_report(start_date, end_date)
        DeviceAnalytics.objects.all().delete()
        DeviceAnalytics.objects.bulk_create([DeviceAnalytics(**obj) for obj in self._device_report])
        return self.list_display

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChannelAnalytics)
class ModelNameAdmin(admin.ModelAdmin):
    _channel_report = []
    list_display = ['channel', 'visitors']
    list_filter = [('range_date', CustomDateRangeFilter), CustomDateFilter]
    ordering = ['-visitors']

    def get_list_display(self, request):
        start_date = request.GET.get('range_date__range__gte')
        end_date = request.GET.get('range_date__range__lte')
        custom_date = request.GET.get('date')
        if custom_date and custom_date in ['1', '2', '3', '4']:
            now_date = now().date()
            if custom_date == '1':
                start_date = str(now_date)
                end_date = str(now_date + datetime.timedelta(days=1))
            elif custom_date == '2':
                start_date = str(now_date - datetime.timedelta(days=7))
                end_date = str(now_date + datetime.timedelta(days=1))
            elif custom_date == '3':
                start_date = str(now_date.replace(day=1))
                now_date_month = now_date.month
                next_month = now_date.month + 1 if now_date_month < 12 else 1
                end_date = str(now_date.replace(day=1, month=next_month))
            else:
                start_date = str(now_date.replace(month=1, day=1))
                end_date = str(now_date.replace(year=now_date.year + 1, month=1, day=1))
        else:
            if start_date:
                validate_date(start_date)
            if end_date:
                validate_date(end_date)
        self._channel_report = GoogleAnalytics.channels_report(start_date, end_date)
        ChannelAnalytics.objects.all().delete()
        ChannelAnalytics.objects.bulk_create([ChannelAnalytics(**obj) for obj in self._channel_report])
        return self.list_display

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
