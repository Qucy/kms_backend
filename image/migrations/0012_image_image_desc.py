# Generated by Django 3.2.14 on 2022-08-17 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('image', '0011_merge_20220817_1006'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='image_desc',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
