# Generated by Django 5.1.7 on 2025-04-21 03:25

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0005_alter_purchase_datetime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchase',
            name='datetime',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
