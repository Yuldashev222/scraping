from django.contrib import admin
from django.utils.html import format_html

from scraping.models import Scraping, UnnecessaryFile


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


@admin.register(UnnecessaryFile)
class UnnecessaryFileAdmin(admin.ModelAdmin):
    list_display = ['website_link', 'pdf_source_link']
    list_filter = ['inform']
    list_display_links = None

    def website_link(self, obj):
        if obj.inform:
            return format_html(f"<a target='_blank' href='{obj.inform.link}'>{obj.inform.link}")
        return None

    def pdf_source_link(self, obj):
        return format_html(f"<a target='_blank' href='{obj.pdf_link}'>{obj.pdf_link}")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
