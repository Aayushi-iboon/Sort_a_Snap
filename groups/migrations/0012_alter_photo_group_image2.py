# Generated by Django 5.1.3 on 2024-11-28 13:41

import groups.model.group
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0011_photo_group_image2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo_group',
            name='image2',
            field=models.ImageField(blank=True, null=True, upload_to=groups.model.group.user_image_upload_path),
        ),
    ]
