# Generated by Django 5.1.5 on 2025-02-14 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0016_merge_20250214_2240'),
    ]

    operations = [
        migrations.CreateModel(
            name='Amenity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amenity_name', models.CharField(max_length=100, verbose_name='Tên tiện ích')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Mô tả')),
                ('icon', models.CharField(blank=True, max_length=50, null=True, verbose_name='Icon')),
            ],
            options={
                'verbose_name': 'Tiện ích',
                'verbose_name_plural': 'Tiện ích',
            },
        ),
        migrations.RemoveField(
            model_name='payment',
            name='note',
        ),
    ]
