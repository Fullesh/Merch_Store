# Generated by Django 4.2 on 2025-02-15 06:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('merch_store', '0002_merch'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='coins',
            field=models.IntegerField(default=1000, verbose_name='Монеты'),
        ),
    ]
