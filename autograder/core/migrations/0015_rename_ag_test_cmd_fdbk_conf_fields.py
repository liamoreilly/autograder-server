# Generated by Django 2.0.1 on 2018-06-04 16:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_add_new_ag_test_case_fdbk_conf_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='agtestcommand',
            old_name='normal_fdbk_config',
            new_name='old_normal_fdbk_config',
        ),
        migrations.RenameField(
            model_name='agtestcommand',
            old_name='past_limit_submission_fdbk_config',
            new_name='old_past_limit_submission_fdbk_config',
        ),
        migrations.RenameField(
            model_name='agtestcommand',
            old_name='staff_viewer_fdbk_config',
            new_name='old_staff_viewer_fdbk_config',
        ),
        migrations.RenameField(
            model_name='agtestcommand',
            old_name='ultimate_submission_fdbk_config',
            new_name='old_ultimate_submission_fdbk_config',
        ),
    ]