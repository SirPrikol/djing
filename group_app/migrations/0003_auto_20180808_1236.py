# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-08 12:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group_app', '0002_group_code'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'ordering': ('title',), 'verbose_name': 'Group', 'verbose_name_plural': 'Groups'},
        ),
    ]
