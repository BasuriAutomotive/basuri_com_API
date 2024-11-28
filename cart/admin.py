from django.contrib import admin
from .models import Cart, CartItem
from base.admin import BaseAdmin

class CartAdmin(BaseAdmin):
    list_display = ('cart_id', 'date_added', 'is_active')  # Showing cart_id and date added
    search_fields = ('cart_id',)
    list_filter = ('date_added',)


class CartItemAdmin(BaseAdmin):
    list_display = ('user', 'product', 'cart', 'quantity', 'is_active')  # Showing user, product, cart, quantity, and status
    search_fields = ('user__email', 'product__name', 'cart__cart_id')  # Search by user, product, and cart
    list_filter = ('is_active', 'cart', 'user', 'product')  # Filter by cart, user, product, and is_active

    def sub_total(self, obj):
        return obj.product.productprice_set.first().value * obj.quantity  # Assuming product has prices
    sub_total.short_description = 'Sub Total'  # Custom column name


# Registering the models with their corresponding admin classes
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)