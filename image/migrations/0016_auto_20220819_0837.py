# Generated by Django 3.2.14 on 2022-08-19 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('image', '0015_auto_20220817_1049'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='creation_datetime',
            field=models.DateTimeField(verbose_name='datetime image uploaded'),
        ),
        migrations.AlterField(
            model_name='image',
            name='creation_datetime',
            field=models.DateTimeField(verbose_name='datetime image uploaded'),
        ),
    ]