# Generated by Django 5.1.2 on 2025-01-02 04:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0004_remove_order_tracking_number_shipment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='shipment',
            options={'ordering': ['created_at']},
        ),
        migrations.RemoveField(
            model_name='shipment',
            name='shipment_created_date',
        ),
    ]