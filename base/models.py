from django.db import models
from .managers import BaseManager

# BASE MODEL FOR TRACKING DATA ACTIVITY
class Base(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)  # Field for soft delete

    class Meta:
        abstract = True

    objects = BaseManager()

    def delete(self, *args, **kwargs):
        """
        Override the delete method to implement soft delete.
        Sets `is_deleted` to True instead of removing the object from the database.
        """
        self.is_deleted = True
        self.save()

    def restore(self, *args, **kwargs):
        """
        Method to restore a soft-deleted object by setting `is_deleted` to False.
        """
        self.is_deleted = False
        self.save()
        

# BASE MODEL FOR META SEO FIELDS
class MetaSEO(models.Model):
    meta_title = models.CharField(blank=True, null=True, max_length=255)
    meta_description = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True
