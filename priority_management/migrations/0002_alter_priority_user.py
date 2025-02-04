# Generated by Django 5.1.5 on 2025-02-04 14:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_remove_customuser_phone_number_and_more'),
        ('priority_management', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='priority',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser'),
        ),
    ]
