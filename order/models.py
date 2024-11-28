from django.db import models
from accounts.models import Account
from product.models import Product, Currencies
from base.models import Base
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

class OrderStatus(Base):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.URLField(max_length=255, blank=True, null=True)
    def __str__(self):
        return self.name


class Order(Base):

    CHECKOUT_CHOICES = [
        ('cart', 'Cart'),
        ('direct', 'Direct Checkout'),
    ]

    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    billing_address = models.CharField(max_length=20, blank=True)
    shipping_address = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)])
    currency = models.ForeignKey(Currencies, default=None, on_delete=models.CASCADE, null=True)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)])
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    order_number = models.CharField(max_length=30)
    so_number = models.CharField(max_length=30, null=True, blank=True)
    order_note = models.CharField(max_length=100, blank=True, null=True)
    ip = models.CharField(blank=True, max_length=30)
    checkout_type = models.CharField(max_length=10, choices=CHECKOUT_CHOICES, default='cart', null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0.00)])
    tracking_number = models.CharField(max_length=100, blank=True, null=True)

    provider_order_id = models.CharField(_("Order ID"), max_length=40, null=True, blank=True, default="")
    payment_id = models.CharField(_("Payment ID"), max_length=36, null=True, blank=True, default="")
    signature_id = models.CharField(_("Signature ID"), max_length=128, null=True, blank=True, default="")

    def add_status(self, status):
        current_position = self.status_history.count() + 1  # Get the next position based on current history count
        OrderStatusHistory.objects.create(order=self, status=status, position=current_position)


class OrderItem(Base):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)


class OrderStatusHistory(Base):
    order = models.ForeignKey(Order, related_name='status_history', on_delete=models.CASCADE)
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)  # Reference to the OrderStatus model
    changed_at = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField()  # Tracks the sequence of status updates

    class Meta:
        ordering = ['position']  # Ensures history is ordered by position

    def save(self, *args, **kwargs):
        # Automatically set the position to be +1 of the last position in the order's history
        if not self.position:
            last_position = OrderStatusHistory.objects.filter(order=self.order).count()
            self.position = last_position + 1  # Increment position by 1
        
        super(OrderStatusHistory, self).save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order.order_number} - {self.status.name} at {self.changed_at} (Position {self.position})"
