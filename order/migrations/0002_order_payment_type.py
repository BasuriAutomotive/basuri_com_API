# Generated by Django 5.1.2 on 2024-12-25 12:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_type',
            field=models.CharField(default='paypal', max_length=20),
        ),
    ]