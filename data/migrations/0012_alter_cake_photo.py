# Generated by Django 4.2.18 on 2025-03-01 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0011_alter_cake_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cake',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='media/cakes/', verbose_name='Фото торта'),
        ),
    ]
