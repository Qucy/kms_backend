# Generated by Django 4.0.5 on 2022-07-04 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_name', models.CharField(max_length=50)),
                ('image_type', models.CharField(max_length=20)),
                ('image_size', models.PositiveBigIntegerField(default=0)),
                ('image_width', models.PositiveBigIntegerField(default=0)),
                ('image_height', models.PositiveBigIntegerField(default=0)),
                ('image_url', models.CharField(max_length=200)),
                ('image_desc', models.CharField(max_length=200)),
                ('image_thumbnail', models.BinaryField()),
                ('create_by', models.CharField(max_length=10)),
                ('creation_datetime', models.DateTimeField(verbose_name='datetime image uploaded')),
            ],
        ),
        migrations.CreateModel(
            name='ImageTagLinkage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_id', models.IntegerField()),
                ('tag_id', models.IntegerField()),
                ('create_by', models.CharField(max_length=10)),
                ('creation_datetime', models.DateTimeField(verbose_name='datetime linkage created')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag_name', models.CharField(max_length=200)),
                ('tag_category', models.CharField(max_length=50)),
                ('create_by', models.CharField(max_length=10)),
                ('creation_datetime', models.DateTimeField(verbose_name='datetime tag created')),
            ],
        ),
        migrations.AddConstraint(
            model_name='tag',
            constraint=models.UniqueConstraint(fields=('tag_name',), name='tag name unique constraint'),
        ),
        migrations.AddIndex(
            model_name='imagetaglinkage',
            index=models.Index(fields=['image_id'], name='image_id_idx'),
        ),
        migrations.AddIndex(
            model_name='imagetaglinkage',
            index=models.Index(fields=['tag_id'], name='tag_id_idx'),
        ),
        migrations.AddConstraint(
            model_name='imagetaglinkage',
            constraint=models.UniqueConstraint(fields=('image_id', 'tag_id'), name='image and tag link constraint'),
        ),
        migrations.AddConstraint(
            model_name='image',
            constraint=models.UniqueConstraint(fields=('image_name',), name='image name unique constraint'),
        ),
    ]
