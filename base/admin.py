from django.contrib import admin

class BaseAdmin(admin.ModelAdmin):
    list_display = ('is_active', 'is_deleted', 'created_at', 'updated_at', 'created_by', 'updated_by')
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('is_active', 'is_deleted')

    actions = ['restore_selected', 'soft_delete_selected']

    def soft_delete_selected(self, request, queryset):
        """
        Custom admin action to perform soft delete on selected objects.
        """
        queryset.update(is_deleted=True)
        self.message_user(request, "Selected records have been soft deleted.")
    
    soft_delete_selected.short_description = "Soft delete selected records"

    def restore_selected(self, request, queryset):
        """
        Custom admin action to restore soft-deleted objects.
        """
        queryset.update(is_deleted=False)
        self.message_user(request, "Selected records have been restored.")
    
    restore_selected.short_description = "Restore selected soft-deleted records"
