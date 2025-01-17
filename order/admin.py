from django.contrib import admin

from .models import Order, OrderItem, OrderStatus, OrderStatusHistory, OrderAction, Shipment
from base.admin import BaseAdmin

class OrderItemInline(admin.TabularInline):
    """Inline admin view for OrderItem"""
    model = OrderItem
    extra = 1


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline admin view for OrderStatusHistory"""
    model = OrderStatusHistory
    extra = 0 
    readonly_fields = ('changed_at', 'position')
    can_delete = False

class ShipmentInline(admin.TabularInline):
    """Inline admin view for Shipment"""
    model = Shipment
    extra = 0
    readonly_fields = ('shipment_created_date',)
    fields = ('logistic_name', 'tracking_number', 'shipment_created_date', 'additional_info')
    can_delete = True


@admin.register(Order)
class OrderAdmin(BaseAdmin):
    """Admin view for Order"""
    list_display = ('order_number', 'user', 'checkout_type', 'total_amount', 'order_date', 'total_amount', 'is_paid', 'so_number')
    list_filter = BaseAdmin.list_filter + ('is_paid', 'checkout_type', 'currency')
    search_fields = ('order_number', 'user__email', 'so_number')
    readonly_fields = BaseAdmin.readonly_fields + ('order_number', 'order_date', 'payment_date', 'provider_order_id', 'payment_id', 'signature_id')

    inlines = [OrderItemInline, OrderStatusHistoryInline]


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


@admin.register(Shipment)
class ShipmentAdmin(BaseAdmin):
    """Admin view for Shipment"""
    list_display = ('order', 'logistic_name', 'tracking_number', 'created_at')
    search_fields = ('order__order_number', 'logistic_name', 'tracking_number')
    readonly_fields = BaseAdmin.readonly_fields
    fields = ('order', 'logistic_name', 'tracking_number', 'created_at', 'notes')

@admin.register(OrderAction)
class OrderActionAdmin(admin.ModelAdmin):
    list_display = ('order__order_number', 'action_name', 'status', 'updated_at', 'details')
    list_filter = ('action_name', 'status', 'updated_at')
    search_fields = ('order__order_id', 'action_name', 'details')
    ordering = ('-updated_at',)