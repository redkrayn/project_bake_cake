# Generated by Django 5.1.6 on 2025-03-02 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0018_cake_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='cake',
            name='purchase_count',
            field=models.IntegerField(default=0),
        ),
    ]
