from django.contrib import admin

from .models import Category, Product, ProductGallery, ProductPrice, Attribute, ProductAttribute
from base.admin import BaseAdmin

class CategoryAdmin(BaseAdmin):
    list_display = ('name', 'slug', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}  # Automatically generates slug from the name field


class ProductAdmin(BaseAdmin):
    list_display = ('name', 'sku', 'category', 'vendor', 'is_available', 'stock_quantity', 'is_active', 'is_deleted')
    list_filter = ('is_available', 'category', 'is_active')  # Adding a filter by category
    search_fields = ('name', 'sku', 'vendor')
    prepopulated_fields = {'slug': ('name',)}
    
    # Make these fields editable directly in the list view
    list_editable = ('is_available', 'stock_quantity', 'is_active', 'category')

    # Add the ability to filter by category in the product admin list
    list_select_related = ('category',)  # Optimizes performance when displaying related foreign keys


class ProductGalleryAdmin(BaseAdmin):
    list_display = ('product', 'file', 'type', 'position', 'alt', 'is_active')
    search_fields = ('product__name', 'alt')


class ProductPriceAdmin(BaseAdmin):
    list_display = ('product', 'currencies', 'value', 'is_active')
    search_fields = ('product__name', 'currencies__code')
    list_filter = ('currencies',)


# Registering the models with their corresponding admin classes
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductGallery, ProductGalleryAdmin)
admin.site.register(ProductPrice, ProductPriceAdmin)

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Display the name in the list view
    search_fields = ('name',)  # Add a search bar for the name field
    ordering = ('name',)  # Order attributes alphabetically by name

@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('product', 'attribute', 'value', 'value_text', 'position')  # Columns in list view
    list_filter = ('attribute',)  # Add a filter sidebar for the attribute field
    search_fields = ('product__name', 'attribute__name', 'value', 'value_text')  # Add a search bar
    ordering = ('position',)  # Order by the position field
    autocomplete_fields = ('product', 'attribute')
