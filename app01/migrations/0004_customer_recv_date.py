# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-27 01:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0003_courserecord_paymentrecord_student_studyrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='recv_date',
            field=models.DateField(blank=True, null=True, verbose_name='接客时间'),
        ),
    ]
