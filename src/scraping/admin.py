from django.contrib import admin

from scraping.models import Scraping


@admin.register(Scraping)
class ScrapingAdmin(admin.ModelAdmin):
    list_display = ['play', 'pause_inform_id']
    list_editable = ['play']
    list_display_links = None
    readonly_fields = ['pause_inform_id']

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
