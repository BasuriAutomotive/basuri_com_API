# Generated by Django 5.1.2 on 2025-01-08 10:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0005_attribute_product_parent_sku_productattribute'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productattribute',
            old_name='value_name',
            new_name='value_text',
        ),
    ]
