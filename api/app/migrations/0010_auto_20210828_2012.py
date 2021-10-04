# Generated by Django 3.2.5 on 2021-08-29 00:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_goal_subscribed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='goal',
            name='subscribed',
        ),
        migrations.AddField(
            model_name='user',
            name='subscribed',
            field=models.BooleanField(default=True),
        ),
    ]