from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from .validators import validate_link
from .enums import InformCountry, InformRegion, ORGANS
from .services import file_upload_location, extract_zip_file


class ZipFileUpload(models.Model):
    zip_file = models.FileField(
        upload_to='zip_files/', validators=[FileExtensionValidator(allowed_extensions=['zip'])]
    )
    pdfs_count = models.PositiveSmallIntegerField(blank=True, default=0)
    is_completed = models.BooleanField(verbose_name='är klart', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if (
                (
                        ZipFileUpload.objects.filter(is_completed=False).exists()
                        and
                        not self.pk
                )
                or
                Inform.objects.filter(is_completed=False).exists()
        ):
            raise ValidationError('den sista länken är inte klar än')

    def __str__(self):
        return f'{self.created_at}'

    def save(self, *args, **kwargs):
        created = True if not self.pk else False
        super().save(*args, **kwargs)
        if created:
            extract_zip_file(self.zip_file.path, self.id)


class Logo(models.Model):
    country = models.CharField(verbose_name='Län', max_length=3, choices=InformCountry.choices())
    region = models.CharField(verbose_name='Komun', max_length=7, choices=InformRegion.choices(), unique=True)
    logo = models.FileField(upload_to='logos/')

    def __str__(self):
        return self.get_region_display()

    def clean(self):
        if self.country and self.region and self.region[:3] != self.country:
            raise ValidationError({'region': 'country has no such region.'})


class Inform(models.Model):
    country = models.CharField(verbose_name='Län', max_length=3, choices=InformCountry.choices())
    region = models.CharField(verbose_name='Komun', max_length=7, choices=InformRegion.choices())
    organ = models.CharField(max_length=1, choices=ORGANS, blank=True, null=True)
    link = models.URLField(max_length=400, unique=True, validators=[validate_link])
    desc = models.CharField(max_length=500, blank=True)
    pdfs_count = models.PositiveSmallIntegerField(default=0)
    date_created = models.DateTimeField('date added', auto_now_add=True)
    is_completed = models.BooleanField(verbose_name='är klart', default=False)
    new_pdfs = models.BooleanField(default=True)
    last_pdf = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.pk}: {self.link}'

    class Meta:
        verbose_name = 'länk'
        verbose_name_plural = 'länkar'

    def clean(self):
        if (
                (
                        Inform.objects.exclude(pk=self.pk).filter(is_completed=False).exists()  # last
                        and
                        (
                                not self.pk
                                or
                                self.pk and self.link != Inform.objects.get(pk=self.pk).link
                        )
                )
                or
                ZipFileUpload.objects.filter(is_completed=False).exists()
        ):
            raise ValidationError('den sista länken är inte klar än')

        if self.country and self.region and self.region[:3] != self.country:
            raise ValidationError({'region': 'country has no such region.'})

        if not Logo.objects.filter(region=self.region).exists():
            raise ValidationError(f'{self.get_region_display()} Logo Not found')


class FileDetail(models.Model):
    country = models.CharField(verbose_name='Län', max_length=3, choices=InformCountry.choices())
    region = models.CharField(verbose_name='Komun', max_length=7, choices=InformRegion.choices())
    organ = models.CharField(max_length=1, choices=ORGANS)
    file = models.FileField(
        upload_to=file_upload_location, max_length=500,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    text = models.TextField(blank=True)
    first_page_text = models.TextField(blank=True)
    pages = models.PositiveSmallIntegerField(blank=True, null=True)
    size = models.FloatField(blank=True, null=True)
    source_file_link = models.URLField(blank=True, null=True, max_length=400)
    file_date = models.DateField(null=True, blank=True)
    is_scanned = models.BooleanField(verbose_name='skannade', default=False)
    is_active = models.BooleanField(default=False)

    inform = models.ForeignKey(Inform, verbose_name='LÄNK ID', on_delete=models.CASCADE, blank=True, null=True)
    zip_file = models.ForeignKey(
        ZipFileUpload, verbose_name='Zip File', on_delete=models.CASCADE, blank=True, null=True
    )
    logo = models.ForeignKey(Logo, verbose_name='Logotype', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.file)

    def clean(self):
        if self.country and self.region and self.region[:3] != self.country:
            raise ValidationError({'region': 'country has no such region.'})

        if not self.pk and FileDetail.objects.filter(pages__isnull=True).exists():
            raise ValidationError('last file process extract text')

    class Meta:
        verbose_name = 'fil'
        verbose_name_plural = 'filer'


class SearchDetail(models.Model):
    text = models.CharField(max_length=600)
    result_files_cnt = models.PositiveIntegerField(verbose_name='antal filer hittade')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='datum sökt efter')
    ipaddress = models.CharField(verbose_name='Client IP', blank=True, max_length=50)

    def __str__(self):
        return self.text[:30]


class IgnoreFile(models.Model):
    link = models.URLField(max_length=500)
    source_file_link = models.URLField(max_length=500)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.source_file_link


class IgnoreText(models.Model):
    text = models.CharField(help_text=_('word in filename'), max_length=255)
    from_filename = models.BooleanField(default=True)

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        self.text = ' '.join(self.text.split()).strip().lower()
        super().save(*args, **kwargs)
