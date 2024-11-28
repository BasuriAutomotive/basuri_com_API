from django.db import models
from base.models import Base
from accounts.models import Account
from product.models import Product
from django.core.validators import MinValueValidator, MaxValueValidator

class Review(Base):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title_comment = models.CharField(max_length=100)
    comment = models.TextField()
    is_accepted = models.BooleanField(default=False)
