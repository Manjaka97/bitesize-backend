# Generated by Django 3.2.5 on 2021-08-28 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20210826_2052'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='subscribed',
            field=models.BooleanField(default=True),
        ),
    ]
