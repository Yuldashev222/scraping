from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import AbstractUser, UserManager, apps
from phonenumber_field.modelfields import PhoneNumberField

from .validators import first_part_validate_ipaddress


class RangeIpAddress(models.Model):
    owner = models.CharField(verbose_name='för vem', max_length=400, blank=True)
    first_part_ipaddress = models.CharField(
        max_length=11, validators=[first_part_validate_ipaddress], help_text='Example: 123.123.123'
    )
    start = models.PositiveSmallIntegerField(validators=[MaxValueValidator(255)])
    end = models.PositiveSmallIntegerField(validators=[MaxValueValidator(255)])
    date_created = models.DateTimeField('date added', auto_now_add=True)

    is_active = models.BooleanField(default=True)
    rate_limit_per_minute = models.PositiveSmallIntegerField(
        verbose_name="Rate limit per minute",
        help_text='How many times per minute can a client send requests?',
        validators=[MinValueValidator(1)],
    )
    rate_limit_per_month = models.PositiveBigIntegerField(
        verbose_name="Rate limit per month",
        help_text='How many times per month can a client send requests?',
        validators=[MinValueValidator(1)]
    )
    minute_requests = models.PositiveIntegerField(default=0)
    current_minute = models.DateTimeField(null=True, blank=True)
    month_requests = models.PositiveBigIntegerField(default=0)
    month_started = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['first_part_ipaddress', 'start', 'end']
        verbose_name_plural = 'Range Ip Addresses'

    def clean(self):
        if self.start and self.end and self.start > self.end:
            raise ValidationError({'start': f'must be less than {self.end}'})
        if self.rate_limit_per_month < self.rate_limit_per_minute:
            raise ValidationError(
                {"rate_limit_per_minute": "Rate limit per minute must be less than per month"}
            )

    def __str__(self):
        return f'{self.first_part_ipaddress}: [{self.start}, {self.end}]'


class CustomUserManager(UserManager):

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given username must be set")
        email = self.normalize_email(email)
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None

    first_name = models.CharField("first name", max_length=150)
    last_name = models.CharField("last name", max_length=150)
    phone_number = PhoneNumberField(blank=True)
    email = models.EmailField(unique=True)

    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    @classmethod
    def default_client_user(cls):
        user, created = cls.objects.get_or_create(email='default@client.com', first_name='fc', last_name='lc')
        if created:
            user.set_password(None)
        return user

    def save(self, *args, **kwargs):
        self.is_superuser = True
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('anställd')
        verbose_name_plural = _('anställda')
