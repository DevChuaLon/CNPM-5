# Generated by Django 5.1.5 on 2025-02-09 15:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0010_alter_podbooking_pod_alter_podbooking_user_booking'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(default='vnpay', max_length=50),
        ),
        migrations.AddField(
            model_name='payment',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='description',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='payment',
            name='pod',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='home.pod'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('pending', 'Đang chờ'), ('completed', 'Thành công'), ('failed', 'Thất bại')], default='pending', max_length=20),
        ),
    ]
