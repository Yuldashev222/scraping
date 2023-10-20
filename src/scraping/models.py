from django.db import models

from main import models as main_models, tasks
from django.core.exceptions import ValidationError


class Scraping(models.Model):
    play = models.BooleanField(default=False)
    pause_inform_id = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Start/Stop'

    def clean(self):
        if (
                self.pk and self.play and not Scraping.objects.get(pk=self.pk).play
                and
                (
                        main_models.Inform.objects.filter(is_completed=False).exists()
                        or
                        main_models.ZipFileUpload.objects.filter(is_completed=False).exists()
                )
        ):
            raise ValidationError('den sista länken är inte klar än')

    def save(self, *args, **kwargs):
        if self.pk and self.play and not Scraping.objects.get(pk=self.pk).play:
            tasks.loop_links.delay(start_inform_id=self.pause_inform_id)
        super().save(*args, **kwargs)


class UnnecessaryFile(models.Model):
    inform = models.ForeignKey(verbose_name='länk', to='main.Inform', on_delete=models.CASCADE)
    pdf_link = models.CharField(max_length=500)
