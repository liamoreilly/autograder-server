# Generated by Django 3.0.5 on 2020-04-21 18:01

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0057_auto_20200319_1420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rerunsubmissionstask',
            name='ag_test_suite_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, help_text='When rerun_all_ag_test_suites is False, specifies which\n                     AGTestSuites should be rerun and which AGTestCases within\n                     those suites should be rerun.\n\n        Data format:\n        {\n            // Note: JSON format requires that keys are strings. Postgres\n            // doesn\'t seem to care, but some JSON serializers might.\n            "<ag_test_suite_pk>": [<ag_test_case_pk>, ...],\n            ...\n        }\n\n        If an ag_test_suite_pk is mapped to an empty list, then all ag test cases\n        belonging to that ag test suite will be rerun.'),
        ),
    ]
