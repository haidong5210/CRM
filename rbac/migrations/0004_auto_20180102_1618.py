# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-02 08:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0003_auto_20180102_1616'),
    ]

    operations = [
        migrations.AlterField(
            model_name='permission',
            name='title',
            field=models.CharField(max_length=32, verbose_name='权限名称'),
        ),
    ]
