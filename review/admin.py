from django.contrib import admin
from .models import Review
from base.admin import BaseAdmin

class ReviewAdmin(BaseAdmin):
    list_display = ('user', 'name', 'product', 'rating', 'title_comment', 'is_accepted', 'is_deleted', 'created_at')  # Showing user, product, rating, and acceptance status
    search_fields = ('user__email', 'name', 'product__name', 'title_comment')  # Allow searching by user email, product name, and title comment
    list_filter = ('rating', 'is_accepted', 'created_at')  # Filter reviews by rating, acceptance, and creation date
    ordering = ('-created_at',)  # Order by newest reviews first
    readonly_fields = ('created_at', 'updated_at')  # Making created_at and updated_at read-only in the admin

# Registering the Review model with the corresponding admin class
admin.site.register(Review, ReviewAdmin)
