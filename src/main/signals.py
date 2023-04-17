import os

from django.dispatch import receiver
from django.db.models.signals import post_delete

from .models import FileDetail, Logo


@receiver(post_delete, sender=FileDetail)
def delete_file(instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)


@receiver(post_delete, sender=Logo)
def delete_logo(instance, **kwargs):
    if instance.logo and os.path.isfile(instance.logo.path):
        os.remove(instance.logo.path)
