import os
from django.dispatch import receiver
from django.db.models.signals import post_delete

from .models import FileDetail, Logo, ZipFileUpload


@receiver(post_delete, sender=FileDetail)
def delete_file(instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)


@receiver(post_delete, sender=Logo)
def delete_logo(instance, **kwargs):
    if instance.logo and os.path.isfile(instance.logo.path):
        os.remove(instance.logo.path)


@receiver(post_delete, sender=ZipFileUpload)
def delete_file(instance, **kwargs):
    if instance.zip_file and os.path.isfile(instance.zip_file.path):
        os.remove(instance.zip_file.path)
