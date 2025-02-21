from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import validate_email
from django.db import models
from .managers import AccountManager
from base.models import Base


from django.db import models


class Account(AbstractBaseUser, PermissionsMixin, Base):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('developer', 'Developer'),
        ('super_admin', 'Super Admin'),
    ]

    email = models.EmailField(unique=True, max_length=255, validators=[validate_email])
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')  # User role field
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = AccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']

    def __str__(self):
        return self.email
    

class Profile(Base):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    image = models.URLField(max_length=255, blank=True, null=True)
    country = models.CharField(blank=True, max_length=30, null=True)
    phone_code = models.CharField(max_length=10, blank=True, null=True)  # Phone extension

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.email}"