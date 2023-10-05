from django.contrib import admin
from django.contrib.auth.models import Group

from .models import CustomUser, RangeIpAddress

admin.site.unregister(Group)
admin.site.site_header = 'Offentligabeslut site admin'


@admin.register(RangeIpAddress)
class RangeIpAddressAdmin(admin.ModelAdmin):
    list_display = ('first_part_ipaddress', 'start', 'end', 'date_created', 'owner')
    list_display_links = ('owner', 'first_part_ipaddress', 'date_created')
    search_fields = ('owner',)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'date_joined')
    list_display_links = ('email',)
    search_fields = ['first_name', 'last_name', 'email']
    fields = (
        'first_name',
        'last_name',
        'email',
        'password',
        'phone_number',
        'is_active',
        'date_joined',
    )
    readonly_fields = ('date_joined',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.is_staff = True
            obj.set_password(obj.password)
        elif obj.password != CustomUser.objects.get(pk=obj.pk).password:
            obj.set_password(obj.password)
        obj.save()

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)

    def has_delete_permission(self, request, obj=None):
        return False
