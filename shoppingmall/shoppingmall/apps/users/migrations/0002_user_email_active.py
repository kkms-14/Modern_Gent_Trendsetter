# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2024-03-29 08:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_active',
            field=models.BooleanField(default=False, verbose_name='邮箱激活状态'),
        ),
    ]
