# Generated by Django 2.0.1 on 2018-04-27 18:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_rename_submission_group_invitation'),
    ]

    operations = [
        migrations.RenameField(
            model_name='submission',
            old_name='submission_group',
            new_name='group',
        ),
    ]
