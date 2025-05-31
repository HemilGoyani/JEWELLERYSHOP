from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework_simplejwt.tokens import RefreshToken
from backend.utils import validate_file_size

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Please provide valid email address.")
        if not password:
            raise ValueError("Please provide a Password")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        user = self.create_user(email=email, password=password, **extra_fields)
        user.save()
        return user


class User(AbstractUser):
    AUTH_PROVIDERS = {'facebook': 'facebook', 'google': 'google',
                  'twitter': 'twitter', 'email': 'email'}
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    USER_TYPE = [("PRIMIUM", "PRIMIUM"), ("SEMIPRIMIUM", "SEMIPRIMIUM")]
    username = None
    first_name = models.CharField(max_length=255, null=True, blank=False)
    last_name = models.CharField(max_length=255, null=True, blank=False)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=False)
    user_type = MultiSelectField(
        max_length=255, 
        choices=USER_TYPE, 
        default=["SEMIPRIMIUM"]
    )
    phone_number = PhoneNumberField(
        verbose_name="Phone no.",
        help_text="Provide a number with country code (e.g. +12125552368).",
        unique=True,
        null=True, 
        blank=False
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=False)
    city = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    image = models.ImageField(
        upload_to="user_profile/",
        null=True,
        blank=True,
        validators=[validate_file_size],
    )
    auth_provider = models.CharField(
        max_length=255, blank=False,
        null=False, default=AUTH_PROVIDERS.get('email'))
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number"]

    objects = UserManager()

    @property
    def is_site_admin(self):
        return self.is_superuser
    
    class Meta:
        unique_together = ("email", "phone_number")
        db_table = "user"

    def __str__(self):
        if self.email:
            return str(f"{self.email} {self.phone_number}")
        elif self.first_name:
            return str(f"{self.first_name} {self.phone_number}")
        else:
            return str(self.email)
    
    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }