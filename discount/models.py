from django.db import models
from base.models import Base
from accounts.models import Account

class Coupon(Base):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.FloatField()
    valid_from = models.DateField()
    valid_to = models.DateField()
    used_by = models.ManyToManyField(Account, blank=True)

    def calculate_discount_amount(self, order_total):
        try:
            order_total = float(order_total)
            discount_percentage = float(self.discount_percentage)
        except ValueError:
            return 0 
        # CALCULATE DISCOUNT AMAOUNT BASED ON DISCOUNT PERCENTAGE
        return (discount_percentage / 100) * order_total
    
    def __str__(self):
        return self.code