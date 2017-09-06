# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-08-30 15:24
from __future__ import unicode_literals

import autograder.core.fields
import autograder.core.models.ag_model_base
import autograder.core.models.project.download_task
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_squashed_0014_auto_20170825_1709'),
    ]

    operations = [
        migrations.CreateModel(
            name='DownloadTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('progress', models.IntegerField(default=0, help_text='A percentage indicating how close the task is to completion.', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('error_msg', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('download_type', autograder.core.fields.EnumField(enum_type=autograder.core.models.project.download_task.DownloadType)),
                ('result_filename', models.TextField(blank=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='download_tasks', to='core.Project')),
            ],
            options={
                'abstract': False,
            },
            bases=(autograder.core.models.ag_model_base.ToDictMixin, models.Model),
        ),
    ]