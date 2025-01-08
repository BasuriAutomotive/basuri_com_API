from django.db import models
from base.models import Base, MetaSEO
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.urls import reverse

from utils.models import Currencies


def create_slug(instance, new_slug=None):
    slug = slugify(instance.name)
    if new_slug is not None:
        slug = new_slug
    instance_model = type(instance)
    qs = instance_model.objects.filter(slug=slug)
    exists = qs.exists()
    if exists:
        new_slug = "%s-%s" % (slug, qs.first().id)
        return create_slug(instance, new_slug=new_slug)
    return slug


def pre_save_slug_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = create_slug(instance)


class Category(Base, MetaSEO):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.URLField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def get_url(self):
        return reverse('products_by_category', args=[self.slug])

    def __str__(self):
        return self.name


def pre_save_slug_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = create_slug(instance)


class Product(Base, MetaSEO):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=10, unique=True,)
    parent_sku = models.CharField(max_length=15, null=True)
    vendor = models.CharField(max_length=20, default='Basuri Automotive')
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField()


    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.name



pre_save.connect(pre_save_slug_receiver, sender=Category)
pre_save.connect(pre_save_slug_receiver, sender=Product)


class ProductGallery(Base):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='product_gallery', null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    file = models.URLField(max_length=500, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    position = models.IntegerField()
    alt = models.CharField(max_length=200, blank=True, null=True)


class ProductPrice(Base):
    product = models.ForeignKey(
        Product, default=None, on_delete=models.CASCADE)
    currencies = models.ForeignKey(
        Currencies, default=None, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=12, decimal_places=2)

# Model for Attribute
class Attribute(Base):
    name = models.CharField("Name", max_length=50)

    def __str__(self):
        return self.name


# Model for Property
class ProductAttribute(Base):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='product_property')
    attribute = models.ForeignKey(
        Attribute, on_delete=models.SET_NULL, null=True, related_name='property_attribute')
    value = models.CharField(max_length=150)
    value_text = models.CharField(max_length=150,blank=True,null=True)
    position=models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.attribute.name