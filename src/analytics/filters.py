from django.contrib import admin
from rangefilter.filters import DateRangeFilter


class CustomDateRangeFilter(DateRangeFilter):
    def queryset(self, request, queryset):
        return queryset


class CityFilter(admin.SimpleListFilter):
    title = 'city'
    parameter_name = 'city'

    def lookups(self, request, model_admin):
        country = request.GET.get('country')
        if not country:
            return ((None, None),)
        return [(obj.city, obj.city) for obj in model_admin.model.objects.filter(country=country)]

    def queryset(self, request, queryset):
        country = request.GET.get('country')
        if country and self.value():
            return queryset.filter(city=self.value())
        return queryset
