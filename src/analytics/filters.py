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
            qs = queryset.filter(city=self.value())
            if qs.exists():
                return qs
        return queryset


class ModelDeviceFilter(admin.SimpleListFilter):
    title = 'model'
    parameter_name = 'model'

    def lookups(self, request, model_admin):
        category = request.GET.get('category')
        if not category:
            return ((None, None),)
        return [(obj.model, obj.model) for obj in model_admin.model.objects.filter(category=category)]

    def queryset(self, request, queryset):
        category = request.GET.get('category')
        if category and self.value():
            qs = queryset.filter(model=self.value())
            if qs.exists():
                return qs
        return queryset


class CustomDateFilter(admin.SimpleListFilter):
    title = 'date'
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        return (
            (1, 'Idag'),
            (2, 'Senaste 7 dagarna'),
            (3, 'Denna månad'),
            (4, 'Detta år'),
        )

    def queryset(self, request, queryset):
        return queryset
