# Generated by Django 4.2.18 on 2025-03-01 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0012_alter_cake_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cake',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='.cakes/', verbose_name='Фото торта'),
        ),
    ]
