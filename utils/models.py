import random
from django.db import models
from datetime import timedelta
from django.utils.timezone import now
from django.core.validators import EmailValidator

from accounts.models import Account
from base.models import Base
from address.models import Country


class Currencies(Base):
    currency_type = models.CharField(max_length=10)
    code = models.CharField(max_length=20)
    symbol = models.CharField(max_length=20)
    description = models.CharField(max_length=250)
    is_default = models.BooleanField(default=False)
    countries = models.ManyToManyField(Country, blank=True, related_name="countries")


    def __str__(self):
        return self.code


class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200)
    title = models.CharField(max_length=100, blank=True, null=True) 
    position = models.IntegerField()
    level = models.IntegerField(default=1, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    category = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    def is_parent(self):
        return self.parent is None
    


class OTP(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def is_expired(self):
        """Check if the OTP is expired."""
        return now() > self.expires_at

    @staticmethod
    def generate_otp(user, validity_period=15):
        """
        Generate a new OTP for the user.
        
        Args:
            user: The user for whom the OTP is being generated.
            validity_period: The validity period of the OTP in minutes.
        """
        otp_code = f"{random.randint(100000, 999999)}"
        expires_at = now() + timedelta(minutes=validity_period)

        otp = OTP.objects.create(
            user=user,
            otp_code=otp_code,
            expires_at=expires_at
        )
        return otp


class Newsletter(Base):
    email = models.EmailField(unique=True,validators=[EmailValidator()])
    
    def __str__(self):
        return self.email