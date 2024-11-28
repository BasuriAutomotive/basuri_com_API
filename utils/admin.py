from django.contrib import admin
from .models import Currencies, MenuItem

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