from django.db import models

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

