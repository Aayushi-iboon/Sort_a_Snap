# Generated by Django 5.1.3 on 2024-11-15 11:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imagesense', '0019_alter_contactus_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlackListedToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=500)),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='token_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('token', 'user')},
            },
        ),
    ]
