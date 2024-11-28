from django.db import models
from django.db import models


from base.models import Base
from accounts.models import Profile
from .managers import CountryManager, StateManager



class Country(Base):
    name = models.CharField("Country Name", max_length=50, db_index=True)
    code = models.CharField(
        "Country Code", max_length=10, blank=True, null=True)
    continents = models.CharField(max_length=10, blank=True, null=True, default="AL")
    
    iso3 = models.CharField(max_length=3,blank=True, null=True)
    iso2 = models.CharField(max_length=2,blank=True, null=True)
    numeric_code = models.CharField(max_length=3,blank=True, null=True)
    phone_code = models.CharField(max_length=5,blank=True, null=True)
    capital = models.CharField(max_length=100,blank=True, null=True)
    currency = models.CharField(max_length=5,blank=True, null=True)
    currency_name = models.CharField(max_length=100,blank=True, null=True)
    currency_symbol = models.CharField(max_length=10,blank=True, null=True)
    tld = models.CharField(max_length=10,blank=True, null=True)
    native = models.CharField(max_length=100,blank=True, null=True)
    region = models.CharField(max_length=100,blank=True, null=True)
    region_id = models.PositiveIntegerField(blank=True, null=True)
    subregion = models.CharField(max_length=100,blank=True, null=True)
    subregion_id = models.PositiveIntegerField(blank=True, null=True)
    nationality = models.CharField(max_length=100,blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8,blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8,blank=True, null=True)
    emoji = models.CharField(max_length=10,blank=True, null=True)
    emojiU = models.CharField(max_length=20,blank=True, null=True)

    objects = CountryManager()

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self):
        return self.name


class State(Base):
    name = models.CharField("State Name", max_length=50, db_index=True)
    code = models.CharField("State Code", max_length=10, blank=True, null=True)

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states',blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8,blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8,blank=True, null=True)

    objects = StateManager()

    class Meta:
        verbose_name_plural = "States"
        ordering = ['name']

    def __str__(self):
        return self.name


# USER ADDRESS MODEL
class Address(Base):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    is_default = models.BooleanField(default=False)
