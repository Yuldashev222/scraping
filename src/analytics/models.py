from django.db import models


class VisitorAnalytics(models.Model):
    range_date = models.DateField(null=True)

    def __str__(self):
        return 'changeme'


class CitiesAnalytics(models.Model):
    country = models.CharField(max_length=300)
    city = models.CharField(max_length=300)
    visitors = models.IntegerField()
    range_date = models.DateField(null=True)
