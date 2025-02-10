# Generated by Django 5.1.5 on 2025-02-09 16:49

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_delete_payment'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Số tiền')),
                ('payment_method', models.CharField(choices=[('vnpay', 'VNPay'), ('cash', 'Tiền mặt'), ('transfer', 'Chuyển khoản')], default='vnpay', max_length=20, verbose_name='Phương thức thanh toán')),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='Mã giao dịch')),
                ('status', models.CharField(choices=[('pending', 'Chờ xử lý'), ('completed', 'Thành công'), ('failed', 'Thất bại')], default='pending', max_length=20, verbose_name='Trạng thái')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Thời gian tạo')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Ghi chú')),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.podbooking', verbose_name='Đơn đặt phòng')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Người dùng')),
            ],
            options={
                'verbose_name': 'Thanh toán',
                'verbose_name_plural': 'Thanh toán',
                'ordering': ['-created_at'],
            },
        ),
    ]
