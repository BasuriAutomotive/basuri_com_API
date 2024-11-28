from django.contrib import admin
from .models import Country, State, Address

from base.admin import BaseAdmin


# Custom admin for Country model
@admin.register(Country)
class CountryAdmin(BaseAdmin):
    list_display = ('name', 'code', 'capital', 'currency', 'phone_code', 'is_active', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('name', 'code', 'capital', 'currency')
    list_filter = ('region', 'subregion', 'is_active', 'is_deleted')
    ordering = ('name',)
    fields = ('name', 'code', 'iso3', 'iso2', 'numeric_code', 'phone_code', 
              'capital', 'currency', 'currency_name', 'currency_symbol', 'tld', 
              'native', 'region', 'subregion', 'latitude', 'longitude', 'emoji', 'emojiU',
              'is_active', 'is_deleted', 'created_by', 'updated_by', 'created_at', 'updated_at')


# Custom admin for State model
@admin.register(State)
class StateAdmin(BaseAdmin):
    list_display = ('name', 'code', 'country', 'latitude', 'longitude', 'is_active', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('name', 'code', 'country__name')
    list_filter = ('country', 'is_active', 'is_deleted')
    ordering = ('name',)
    fields = ('name', 'code', 'country', 'latitude', 'longitude', 
              'is_active', 'is_deleted', 'created_by', 'updated_by', 'created_at', 'updated_at')


# Custom admin for Address model
@admin.register(Address)
class AddressAdmin(BaseAdmin):
    list_display = ('profile', 'address_line_1', 'country', 'state', 'city', 'zip_code', 'is_default', 'is_active', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('profile__user__email', 'address_line_1', 'city', 'zip_code')
    list_filter = ('country', 'state', 'is_default', 'is_active', 'is_deleted')
    ordering = ('profile', 'is_default')
    fields = ('profile', 'address_line_1', 'address_line_2', 'country', 'state', 'city', 'zip_code', 
              'contact_person', 'contact_phone', 'is_default', 
              'is_active', 'is_deleted', 'created_by', 'updated_by', 'created_at', 'updated_at')
