# Generated by Django 3.2.5 on 2021-08-10 18:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20210809_1633'),
    ]

    operations = [
        migrations.AddField(
            model_name='step',
            name='user_id',
            field=models.ForeignKey(default='auth0|60ff59b3d056750070d9a58a', on_delete=django.db.models.deletion.CASCADE, to='app.user'),
            preserve_default=False,
        ),
    ]
