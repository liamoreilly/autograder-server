# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-04-17 21:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='autogradertestcasebase',
            name='polymorphic_ctype',
        ),
    ]
