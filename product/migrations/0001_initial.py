# Generated by Django 5.1.2 on 2024-10-14 11:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('utils', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.IntegerField(blank=True, null=True)),
                ('updated_by', models.IntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('meta_title', models.CharField(blank=True, max_length=255, null=True)),
                ('meta_description', models.TextField(blank=True, null=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('image', models.URLField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.IntegerField(blank=True, null=True)),
                ('updated_by', models.IntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('meta_title', models.CharField(blank=True, max_length=255, null=True)),
                ('meta_description', models.TextField(blank=True, null=True)),
                ('name', models.CharField(max_length=255)),
                ('sku', models.CharField(max_length=10, unique=True)),
                ('vendor', models.CharField(default='Basuri Automotive', max_length=20)),
                ('slug', models.SlugField(max_length=200, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_available', models.BooleanField(default=True)),
                ('stock_quantity', models.PositiveIntegerField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.category')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductGallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.IntegerField(blank=True, null=True)),
                ('updated_by', models.IntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('file', models.URLField(blank=True, max_length=500, null=True)),
                ('type', models.CharField(blank=True, max_length=100, null=True)),
                ('p_no', models.IntegerField()),
                ('alt', models.CharField(blank=True, max_length=200, null=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_gallery', to='product.product')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.IntegerField(blank=True, null=True)),
                ('updated_by', models.IntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('value', models.DecimalField(decimal_places=2, max_digits=12)),
                ('currencies', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='utils.currencies')),
                ('product', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='product.product')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
