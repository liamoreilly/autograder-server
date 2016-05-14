# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-14 03:16
from __future__ import unicode_literals

import autograder.core.models.project.uploaded_file
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20160509_0016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadedfile',
            name='file_obj',
            field=models.FileField(max_length=510, upload_to=autograder.core.models.project.uploaded_file._get_project_file_upload_to_path, validators=[autograder.core.models.project.uploaded_file._validate_filename]),
        ),
    ]
