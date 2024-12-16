from django.contrib import admin

from .models import Order, OrderItem, OrderStatus, OrderStatusHistory
from base.admin import BaseAdmin

class OrderItemInline(admin.TabularInline):
    """Inline admin view for OrderItem"""
    model = OrderItem
    extra = 1  # Allows adding one extra item in the admin interface


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline admin view for OrderStatusHistory"""
    model = OrderStatusHistory
    extra = 0  # No extra empty form, just show the history
    readonly_fields = ('changed_at', 'position')  # Make only 'changed_at' and 'position' read-only
    can_delete = False  # Optionally, prevent deletion of status history if needed


@admin.register(Order)
class OrderAdmin(BaseAdmin):
    """Admin view for Order"""
    list_display = ('order_number', 'user', 'total_amount', 'order_date', 'total_amount', 'is_paid', 'so_number', 'tracking_number')
    list_filter = BaseAdmin.list_filter + ('is_paid', 'checkout_type', 'currency')  # Extend BaseAdmin filters
    search_fields = ('order_number', 'user__email', 'tracking_number', 'so_number')
    readonly_fields = BaseAdmin.readonly_fields + ('order_number', 'order_date', 'payment_date', 'provider_order_id', 'payment_id', 'signature_id')

    inlines = [OrderItemInline, OrderStatusHistoryInline]  # Add inlines for OrderItem and OrderStatusHistory


@admin.register(OrderItem)
class OrderItemAdmin(BaseAdmin):
    """Admin view for OrderItem"""
    list_display = ('order', 'product', 'quantity', 'unit_price', 'subtotal')
    search_fields = ('order__order_number', 'product__name')


@admin.register(OrderStatus)
class OrderStatusAdmin(BaseAdmin):
    """Admin view for OrderStatus"""
    list_display = ('name', 'description', 'icon')
    search_fields = ('name', 'description')


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(BaseAdmin):
    """Admin view for OrderStatusHistory"""
    list_display = ('order', 'status', 'changed_at', 'position')
    search_fields = ('order__order_number', 'status__name')
    # readonly_fields = BaseAdmin.readonly_fields + ('order', 'changed_at', 'position')
