import os
from django.contrib import admin, messages
from django.utils.html import format_html
from django_elasticsearch_dsl.registries import registry
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.filters import ChoicesFieldListFilter
from rangefilter.filters import DateRangeFilter, NumericRangeFilter

from .tasks import extract_url_pdf, extract_local_pdf
from . import models


@admin.register(models.ZipFileUpload)
class ZipFileUploadAdmin(admin.ModelAdmin):
    list_display = ['pdfs_count', 'is_completed', 'zip_file', 'created_at']
    list_display_links = ['is_completed', 'created_at']
    list_filter = ['is_completed', 'created_at']
    readonly_fields = ('is_completed', 'pdfs_count')
    list_per_page = 20


@admin.register(models.Logo)
class LogoAdmin(admin.ModelAdmin):
    list_display = ['country', 'region', 'logo_img']
    list_display_links = ['country', 'region']
    list_filter = ['country']
    ordering = ['-id', 'country']
    list_per_page = 50

    def logo_img(self, obj):
        if obj.logo:
            return format_html(f"<a href='{obj.logo.url}'><img width=80 height=45 src='{obj.logo.url}'></a>")

    def save_model(self, request, obj, form, change):
        if obj.pk:
            old_file = models.Logo.objects.get(pk=obj.pk).logo
            if old_file and old_file != obj.logo and os.path.isfile(old_file.path):
                os.remove(old_file.path)
            obj.save()
            files = obj.filedetail_set.all()
            for i in files:
                registry.update(i)
        else:
            obj.save()
            models.FileDetail.objects.filter(region=obj.region).update(logo_id=obj.id)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if obj.filedetail_set.exists():
                return
        queryset.delete()

    def delete_model(self, request, obj):
        if obj.filedetail_set.exists():
            return
        obj.delete()


@admin.register(models.IgnoreText)
class IgnoreTextAdmin(admin.ModelAdmin):
    list_display = ['text', 'from_filename']
    list_filter = ['from_filename']
    list_editable = ['from_filename']
    search_fields = ['text']


@admin.register(models.FileDetail)
class FileDetailAdmin(admin.ModelAdmin):
    list_display = (
       'link_id', 'country', 'region', 'organ', 'file_date', 'pages', 'size', 'file'
    )
    list_display_links = ('country', 'region', 'organ', 'file_date')
    search_fields = ('inform__id',)
    list_per_page = 50
    list_filter = (
        ('file_date', DateRangeFilter),
        ('inform_id', NumericRangeFilter),
        'file_date',
        'organ',
        'country',
        ('region', ChoicesFieldListFilter)
    )
    ordering = ('-id',)

    fields = (
        'file',
        'source_file_link',
        'logo',
        'country',
        'region',
        'organ',
        'file_date',
        'pages',
        'size',
        'text',
    )
    readonly_fields = ('pages', 'logo', 'size', 'text', 'source_file_link')

    def link_id(self, obj):
        if obj.inform:
            return format_html(f"<a target='_blank' href='{obj.inform.link}'>{obj.inform.id}")
        return None

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('inform')

    def delete_queryset(self, request, queryset):
        ignore_files = []
        for obj in queryset:
            if obj.inform and not models.IgnoreFile.objects.filter(
                    link=obj.inform.link, source_file_link=obj.source_file_link
            ).exists():
                ignore_files.append(models.IgnoreFile(link=obj.inform.link, source_file_link=obj.source_file_link))
        queryset.delete()
        models.IgnoreFile.objects.bulk_create(ignore_files)

    def delete_model(self, request, obj):
        if obj.inform and not models.IgnoreFile.objects.filter(
                link=obj.inform.link, source_file_link=obj.source_file_link
        ).exists():
            models.IgnoreFile.objects.create(link=obj.inform.link, source_file_link=obj.source_file_link)
        obj.delete()

    def save_model(self, request, obj, form, change):
        created = False if obj.pk else True
        if not created:
            old_file = models.FileDetail.objects.get(pk=obj.pk).file
            if old_file and old_file != obj.file and os.path.isfile(old_file.path):
                os.remove(old_file.path)
                obj.save()
                extract_local_pdf.delay(obj.id, obj.file.path)
            else:
                obj.save()
        else:
            obj.logo_id = models.Logo.objects.get(region=obj.region).id
            obj.save()
            extract_local_pdf.delay(obj.id, obj.file.path)


@admin.register(models.Inform)
class InformAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'region', 'organ', 'is_completed', 'date_created', 'source_link')
    list_display_links = ('id', 'date_created')
    search_fields = ('link', 'desc')
    list_per_page = 20
    readonly_fields = ('is_completed',)
    search_help_text = 'sök med länk och beskrivning'
    list_filter = (('id', NumericRangeFilter), 'is_completed', 'organ', 'country', 'region')

    def source_link(self, obj):
        return format_html(f"<a href='{obj.link}'>{obj.link}")

    def delete_queryset(self, request, queryset):
        if queryset.filter(is_completed=False).exists():
            self.message_user(
                request,
                _('Among the objects being deleted are incomplete objects'),
                messages.ERROR
            )
            return
        queryset.delete()

    def delete_model(self, request, obj):
        if not obj.is_completed:
            self.message_user(
                request,
                _('the object being deleted is incomplete'),
                messages.ERROR
            )
            return
        obj.delete()

    def save_model(self, request, obj, form, change):
        created = False if obj.pk else True

        if created:
            obj.save()
            extract_url_pdf.delay(obj.link, obj.id)

        else:
            change_link = False
            if obj.link != models.Inform.objects.get(pk=obj.pk).link:
                change_link = True
                models.FileDetail.objects.filter(inform_id=obj.id).delete()
                models.IgnoreFile.objects.filter(link=obj.link).delete()

            obj.save()
            if change_link:
                extract_url_pdf.delay(obj.link, obj.id)


@admin.register(models.SearchDetail)
class SearchDetailAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'ipaddress', 'result_files_cnt', 'text')
    list_display_links = ('date_created',)
    search_fields = ('text',)
    ordering = ('-date_created',)


@admin.register(models.IgnoreFile)
class IgnoreFileAdmin(admin.ModelAdmin):
    list_display = ('source_file_href', 'source_link', 'date_added')
    list_display_links = list_display
    search_fields = ('source_file_link', 'source_link')
    ordering = ('-date_added',)

    def source_file_href(self, obj):
        return format_html(f"<a href='{obj.source_file_link}'>{obj.source_file_link}")

    def source_link(self, obj):
        return format_html(f"<a href='{obj.link}'>{obj.link}")
