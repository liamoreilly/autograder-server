from django.core import exceptions

from autograder.core import constants
from autograder.utils.testing import UnitTestBase
import autograder.core.models as ag_models
import autograder.utils.testing.model_obj_builders as obj_build


class StudentTestSuiteTestCase(UnitTestBase):
    def setUp(self):
        super().setUp()
        self.project = obj_build.make_project()
        self.name = 'qewioruqiwoeiru'

    def test_default_init(self):
        student_suite = ag_models.StudentTestSuite.objects.validate_and_create(
            name=self.name, project=self.project)  # type: ag_models.StudentTestSuite

        self.assertEqual(self.name, student_suite.name)
        self.assertEqual(self.project, student_suite.project)
        self.assertSequenceEqual([], student_suite.project_files_needed.all())
        self.assertTrue(student_suite.read_only_project_files)
        self.assertSequenceEqual([], student_suite.student_files_needed.all())
        self.assertSequenceEqual([], student_suite.buggy_impl_names)

        self.assertFalse(student_suite.use_setup_command)
        self.assertIsInstance(student_suite.setup_command,
                              ag_models.AGCommand)
        self.assertIsInstance(student_suite.get_student_test_names_command,
                              ag_models.AGCommand)
        self.assertEqual(ag_models.StudentTestSuite.DEFAULT_STUDENT_TEST_MAX,
                         student_suite.max_num_student_tests)

        self.assertIsInstance(student_suite.student_test_validity_check_command,
                              ag_models.AGCommand)
        self.assertIsInstance(student_suite.grade_buggy_impl_command,
                              ag_models.AGCommand)

        self.assertEqual(0, student_suite.points_per_exposed_bug)
        self.assertIsNone(student_suite.max_points)
        self.assertFalse(student_suite.deferred)
        self.assertEqual(constants.SupportedImages.default, student_suite.docker_image_to_use)
        self.assertFalse(student_suite.allow_network_access)

        self.assertIsInstance(student_suite.normal_fdbk_config,
                              ag_models.StudentTestSuiteFeedbackConfig)
        self.assertIsInstance(student_suite.ultimate_submission_fdbk_config,
                              ag_models.StudentTestSuiteFeedbackConfig)
        self.assertIsInstance(student_suite.past_limit_submission_fdbk_config,
                              ag_models.StudentTestSuiteFeedbackConfig)
        self.assertIsInstance(student_suite.staff_viewer_fdbk_config,
                              ag_models.StudentTestSuiteFeedbackConfig)

        self.maxDiff = None
        ultimate_fdbk = ag_models.StudentTestSuiteFeedbackConfig.objects.validate_and_create(
            show_invalid_test_names=True,
            show_points=True,
            bugs_exposed_fdbk_level=ag_models.BugsExposedFeedbackLevel.num_bugs_exposed)
        self.assertEqual(ultimate_fdbk.to_dict(),
                         student_suite.ultimate_submission_fdbk_config.to_dict())

        low_fdbk = ag_models.StudentTestSuiteFeedbackConfig.objects.validate_and_create()
        self.assertEqual(low_fdbk.to_dict(),
                         student_suite.normal_fdbk_config.to_dict())

        past_limit_fdbk = student_suite.past_limit_submission_fdbk_config
        self.assertFalse(past_limit_fdbk.show_invalid_test_names)
        self.assertEqual(ag_models.BugsExposedFeedbackLevel.get_min(),
                         past_limit_fdbk.bugs_exposed_fdbk_level)

    def test_valid_init_non_defaults(self):
        proj_file1 = obj_build.make_uploaded_file(self.project)
        proj_file2 = obj_build.make_uploaded_file(self.project)
        student_file = obj_build.make_expected_student_pattern(self.project)
        values = {
            'name': 'adnlakshfdklajhsdlf',
            'project': self.project,
            'project_files_needed': [proj_file1.to_dict(), proj_file2.to_dict()],
            'read_only_project_files': False,
            'student_files_needed': [student_file.to_dict()],
            'buggy_impl_names': ['spam', 'egg', 'sausage', 'waaaaluigi'],
            'setup_command': {'cmd': 'g++ some_stuff.cpp'},
            'get_student_test_names_command': {'cmd': 'ls test_*.cpp'},
            'max_num_student_tests': 30,

            'student_test_validity_check_command': {
                'cmd': 'python3 validity_check.py ${student_test_name}'},
            'grade_buggy_impl_command': {
                'cmd': 'python3 grade.py ${buggy_impl_name} ${student_test_name}'
            },
            'points_per_exposed_bug': 42,
            'max_points': 462,
            'deferred': True,
            'docker_image_to_use': constants.SupportedImages.eecs280,
            'allow_network_access': True,
            'normal_fdbk_config': {
                'bugs_exposed_fdbk_level': (
                    ag_models.BugsExposedFeedbackLevel.num_bugs_exposed.value),
                'show_points': True,
            },
            'ultimate_submission_fdbk_config': {
                'show_setup_stdout': True,
                'show_invalid_test_names': True,
            },
            'past_limit_submission_fdbk_config': {
                'visible': False,
                'show_setup_stderr': True,
            },
            'staff_viewer_fdbk_config': {
                'show_points': False,
            }
        }

        student_suite = ag_models.StudentTestSuite.objects.validate_and_create(
            **values
        )  # type: ag_models.StudentTestSuite

        self.assertCountEqual(
            [uploaded_file['pk'] for uploaded_file in values['project_files_needed']],
            [uploaded_file.pk for uploaded_file in student_suite.project_files_needed.all()])
        values.pop('project_files_needed')

        self.assertCountEqual(
            [pattern['pk'] for pattern in values['student_files_needed']],
            [pattern.pk for pattern in student_suite.student_files_needed.all()])
        values.pop('student_files_needed')

        for key, value in values.items():
            if isinstance(value, dict):
                self.assert_dict_is_subset(value, getattr(student_suite, key).to_dict())
            elif isinstance(value, list):
                self.assertSequenceEqual(value, getattr(student_suite, key))
            else:
                self.assertEqual(value, getattr(student_suite, key))

    def test_suite_ordering(self):
        suite1 = ag_models.StudentTestSuite.objects.validate_and_create(
            name='qweiruquerw', project=self.project)
        suite2 = ag_models.StudentTestSuite.objects.validate_and_create(
            name='xjvnjadoa', project=self.project)

        self.assertCountEqual([suite1.pk, suite2.pk], self.project.get_studenttestsuite_order())

        self.project.set_studenttestsuite_order([suite2.pk, suite1.pk])
        self.assertSequenceEqual([suite2.pk, suite1.pk], self.project.get_studenttestsuite_order())

        self.project.set_studenttestsuite_order([suite1.pk, suite2.pk])
        self.assertSequenceEqual([suite1.pk, suite2.pk], self.project.get_studenttestsuite_order())

    def test_error_name_not_unique(self):
        name = 'spam'
        suite1 = ag_models.StudentTestSuite.objects.validate_and_create(
            name=name, project=self.project)

        with self.assertRaises(exceptions.ValidationError):
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=name, project=self.project)

    def test_max_num_student_tests_out_of_range(self):
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=self.name, project=self.project,
                max_num_student_tests=ag_models.StudentTestSuite.MAX_STUDENT_TEST_MAX + 1)

        self.assertIn('max_num_student_tests', cm.exception.message_dict)

        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=self.name, project=self.project,
                max_num_student_tests=-1)

        self.assertIn('max_num_student_tests', cm.exception.message_dict)

    def test_validity_check_cmd_missing_placeholders(self):
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=self.name, project=self.project,
                student_test_validity_check_command={'cmd': 'no_placeholder'})

        self.assertIn('student_test_validity_check_command', cm.exception.message_dict)

    def test_grade_buggy_impl_command_missing_placeholders(self):
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=self.name, project=self.project,
                grade_buggy_impl_command={
                    'cmd': 'wee {}'.format(
                        ag_models.StudentTestSuite.STUDENT_TEST_NAME_PLACEHOLDER)})

        self.assertIn('grade_buggy_impl_command', cm.exception.message_dict)

        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=self.name, project=self.project,
                grade_buggy_impl_command={
                    'cmd': 'wee {}'.format(
                        ag_models.StudentTestSuite.BUGGY_IMPL_NAME_PLACEHOLDER)})

        self.assertIn('grade_buggy_impl_command', cm.exception.message_dict)

    def test_points_per_exposed_bug_out_of_range(self):
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=self.name, project=self.project,
                points_per_exposed_bug=-1)

        self.assertIn('points_per_exposed_bug', cm.exception.message_dict)

    def test_max_points_out_of_range(self):
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=self.name, project=self.project,
                max_points=-1)

        self.assertIn('max_points', cm.exception.message_dict)

    def test_error_project_file_needed_that_belongs_to_other_project(self):
        other_project = obj_build.make_project(course=self.project.course)
        other_proj_file = obj_build.make_uploaded_file(project=other_project)
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=self.name, project=self.project,
                project_files_needed=[other_proj_file.pk])

        self.assertIn('project_files_needed', cm.exception.message_dict)

    def test_error_student_file_needed_that_belongs_to_other_project(self):
        other_project = obj_build.make_project(course=self.project.course)
        other_student_file = obj_build.make_expected_student_pattern(other_project)
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=self.name, project=self.project,
                student_files_needed=[other_student_file.pk])

        self.assertIn('student_files_needed', cm.exception.message_dict)

    def test_error_stdin_project_file_belongs_to_other_project(self):
        other_project = obj_build.make_project(course=self.project.course)
        other_proj_file = obj_build.make_uploaded_file(project=other_project)

        cmd_json = {
            # This command will satisfy the requirements of the validity check
            # and grade buggy impl commands.
            'cmd': 'echo {} {}'.format(ag_models.StudentTestSuite.STUDENT_TEST_NAME_PLACEHOLDER,
                                       ag_models.StudentTestSuite.BUGGY_IMPL_NAME_PLACEHOLDER),
            'stdin_source': ag_models.StdinSource.project_file.value,
            'stdin_project_file': other_proj_file.pk
        }
        cmd_fields = [
            'setup_command',
            'get_student_test_names_command',
            'student_test_validity_check_command',
            'grade_buggy_impl_command',
        ]
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.StudentTestSuite.objects.validate_and_create(
                name=self.name, project=self.project,
                **{field_name: cmd_json for field_name in cmd_fields})

        for field_name in cmd_fields:
            self.assertIn(field_name, cm.exception.message_dict)

    def test_serialization(self):
        expected_field_names = [
            'pk',
            'name',
            'project',
            'project_files_needed',
            'read_only_project_files',
            'student_files_needed',
            'buggy_impl_names',

            'use_setup_command',
            'setup_command',
            'get_student_test_names_command',
            'max_num_student_tests',

            'student_test_validity_check_command',
            'grade_buggy_impl_command',
            'points_per_exposed_bug',
            'max_points',
            'deferred',
            'docker_image_to_use',
            'allow_network_access',
            'normal_fdbk_config',
            'ultimate_submission_fdbk_config',
            'past_limit_submission_fdbk_config',
            'staff_viewer_fdbk_config',
            'last_modified',
        ]

        proj_file = obj_build.make_uploaded_file(self.project)
        student_file = obj_build.make_expected_student_pattern(self.project)

        student_suite = ag_models.StudentTestSuite.objects.validate_and_create(
            name=self.name, project=self.project,
            setup_command={'cmd': 'setuppy'},
            project_files_needed=[proj_file],
            student_files_needed=[student_file]
        )  # type: ag_models.StudentTestSuite

        serialized = student_suite.to_dict()
        self.assertCountEqual(expected_field_names, serialized.keys())

        self.assertIsInstance(serialized['project_files_needed'][0], dict)
        self.assertIsInstance(serialized['student_files_needed'][0], dict)

        self.assertIsInstance(serialized['setup_command'], dict)
        self.assertIsInstance(serialized['get_student_test_names_command'], dict)
        self.assertIsInstance(serialized['student_test_validity_check_command'], dict)
        self.assertIsInstance(serialized['grade_buggy_impl_command'], dict)
        self.assertIsInstance(serialized['normal_fdbk_config'], dict)
        self.assertIsInstance(serialized['ultimate_submission_fdbk_config'], dict)
        self.assertIsInstance(serialized['past_limit_submission_fdbk_config'], dict)
        self.assertIsInstance(serialized['staff_viewer_fdbk_config'], dict)

        update_dict = student_suite.to_dict()
        non_editable = ['pk', 'project', 'last_modified']
        for field in non_editable:
            update_dict.pop(field)

        student_suite.validate_and_update(**update_dict)