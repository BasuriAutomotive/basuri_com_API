from django.db import models
from django.utils import timezone

class BaseManager(models.Manager):
    """
    A custom manager for models inheriting from the Base model.
    Provides utility methods to filter active, deleted, or all objects.
    """

    def get_query(self):
        """
        Override the default queryset to exclude soft-deleted objects.
        By default, only active (non-deleted) objects will be returned.
        """
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        """
        Return all objects, including those that have been soft-deleted.
        """
        return super().get_queryset()

    def deleted(self):
        """
        Return only the soft-deleted objects.
        """
        return super().get_queryset().filter(is_deleted=True)

    def active(self):
        """
        Return only active (non-deleted) objects.
        """
        return self.get_queryset().filter(is_active=True)

    def inactive(self):
        """
        Return only inactive objects.
        """
        return self.get_queryset().filter(is_active=False)

    def created_by_user(self, user_id):
        """
        Return all objects created by a specific user.
        """
        return self.get_queryset().filter(created_by=user_id)

    def updated_by_user(self, user_id):
        """
        Return all objects updated by a specific user.
        """
        return self.get_queryset().filter(updated_by=user_id)

    def created_after(self, date):
        """
        Return objects created after a certain date.
        """
        return self.get_queryset().filter(created_at__gte=date)

    def created_before(self, date):
        """
        Return objects created before a certain date.
        """
        return self.get_queryset().filter(created_at__lt=date)

    def updated_recently(self):
        """
        Return objects that have been updated recently (within the last 7 days).
        """
        recent = timezone.now() - timezone.timedelta(days=7)
        return self.get_queryset().filter(updated_at__gte=recent)
