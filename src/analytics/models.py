from django.db import models


class VisitorAnalytics(models.Model):
    range_date = models.DateField(null=True)

    def __str__(self):
        return 'changeme'

    class Meta:
        verbose_name_plural = ' VisitorAnalytics'


class CitiesAnalytics(models.Model):
    country = models.CharField(max_length=300)
    city = models.CharField(max_length=300)
    visitors = models.IntegerField()
    range_date = models.DateField(null=True)

    class Meta:
        verbose_name_plural = ' CitiesAnalytics'


class PagesAnalytics(models.Model):
    page_path = models.CharField(max_length=500)
    visitors = models.IntegerField()
    range_date = models.DateField(null=True)

    class Meta:
        verbose_name_plural = ' PagesAnalytics'


class DeviceAnalytics(models.Model):
    category = models.CharField(max_length=500)
    model = models.CharField(max_length=500)
    visitors = models.IntegerField()
    range_date = models.DateField(null=True)

    class Meta:
        verbose_name_plural = ' DeviceAnalytics'


class ChannelAnalytics(models.Model):
    channel = models.CharField(max_length=500)
    visitors = models.IntegerField()
    range_date = models.DateField(null=True)

    class Meta:
        verbose_name_plural = ' ChannelAnalytics'
