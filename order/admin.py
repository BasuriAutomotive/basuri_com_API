from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html


from base.admin import BaseAdmin
from .models import Order, OrderItem, OrderStatus, OrderStatusHistory, OrderAction, Shipment



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


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'checkout_type', 'total_amount', 'order_date', 'is_paid', 'so_number', 'erp_sync_button')
    list_filter = BaseAdmin.list_filter + ('is_paid', 'checkout_type', 'currency')
    search_fields = ('order_number', 'user__email', 'so_number')
    readonly_fields = BaseAdmin.readonly_fields + ('order_number', 'order_date', 'payment_date', 'provider_order_id', 'payment_id', 'signature_id', 'erp_sync_button')

    def erp_sync_button(self, obj):
        """Show a button to trigger ERP sync only if order is paid and so_number is missing."""
        if obj.is_paid and not obj.so_number:
            url = reverse("sync-erp", args=[obj.pk])
            return format_html('<a class="button" style="color: white; background: #28a745; padding: 5px 10px; text-decoration: none; border-radius: 5px;" href="{}">Sync to ERP</a>', url)
        return "ERP Synced" if obj.so_number else "-"

    erp_sync_button.short_description = "ERP Sync"

admin.site.register(Order, OrderAdmin)
