# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-27 03:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0004_customer_recv_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsultDestribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True, verbose_name='跟进日期')),
                ('status', models.IntegerField(choices=[(1, '已成单'), (2, '正在跟进'), (3, '三天未跟进'), (4, '15天未成单')], default=2)),
                ('consultant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='con', to='app01.UserInfo', verbose_name='跟踪人')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cs', to='app01.Customer', verbose_name='客户id')),
            ],
        ),
    ]