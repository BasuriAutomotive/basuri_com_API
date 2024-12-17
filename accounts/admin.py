from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Account, Profile
from django.utils.translation import gettext_lazy as _

# Custom UserAdmin
class AccountAdmin(BaseUserAdmin):
    list_display = ('email', 'phone_number', 'role', 'is_staff', 'is_active', 'is_deleted', 'created_at', 'updated_at')
    list_filter = ('role', 'is_staff', 'is_active', 'is_deleted')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('phone_number', 'role')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important Dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
        (_('Status'), {'fields': ('is_deleted',)}),  # Add is_deleted field to track soft deletion
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login')  # Read-only fields
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password1', 'password2', 'role', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'phone_number', 'role')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')

    def get_queryset(self, request):
        """
        Override the default queryset to include soft-deleted users if needed.
        """
        return super().get_queryset(request).filter(is_deleted=False)  # Exclude soft-deleted users by default

# ProfileAdmin for managing profiles related to users
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'country', 'phone_code', 'otp', 'image')
    search_fields = ('first_name', 'last_name', 'user__email', 'country')
    list_filter = ('country',)
    # readonly_fields = ('user',)  # Prevent editing of the linked user field

    def get_queryset(self, request):
        """
        Make sure soft-deleted users' profiles aren't included unless explicitly wanted.
        """
        return super().get_queryset(request).select_related('user').filter(user__is_deleted=False)

# Register the models in the admin site
admin.site.register(Account, AccountAdmin)
admin.site.register(Profile, ProfileAdmin)
