from django.contrib import admin
from .models import Currencies, MenuItem, OTP

from base.admin import BaseAdmin

@admin.register(Currencies)
class CurrenciesAdmin(BaseAdmin):
    list_display = ('currency_type', 'code', 'symbol', 'is_default', 'is_active', 'is_deleted')
    list_filter = ('is_default', 'countries')
    search_fields = ('currency_type', 'code', 'symbol', 'description')
    filter_horizontal = ('countries',)
    ordering = ('code',)


class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'level', 'position', 'category', 'parent']
    list_filter = ['category']

admin.site.register(MenuItem, MenuItemAdmin)

class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'is_used', 'expires_at', 'created_at')
    list_filter = ('is_used', 'expires_at')
    search_fields = ('user__email', 'otp_code')
    readonly_fields = ('otp_code', 'created_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'otp_code', 'is_used')
        }),
        ('Timestamps', {
            'fields': ('expires_at', 'created_at'),
        }),
    )

admin.site.register(OTP, OTPAdmin)
