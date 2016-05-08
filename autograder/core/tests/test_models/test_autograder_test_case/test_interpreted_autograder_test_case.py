import os
import random
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import exceptions

from autograder.security.autograder_sandbox import AutograderSandbox
import autograder.core.models as ag_models

import autograder.core.shared.utilities as ut

from autograder.core.tests.temporary_filesystem_test_case import (
    TemporaryFilesystemTestCase)
from autograder.core.tests import dummy_object_utils as obj_ut


class _SetUpBase:
    def setUp(self):
        super().setUp()

        self.group = obj_ut.build_submission_group()
        self.project = self.group.project

        self.submitted_filename = 'my_file.py'
        self.project_filename = 'testy.py'

        # self.admin = obj_ut.create_dummy_user()
        # self.project = obj_ut.build_project(
        #     course_kwargs={'administrators': [self.admin]},
        #     project_kwargs={
        #         'required_student_files': [self.submitted_filename]})

        self.project_file = ag_models.UploadedFile.objects.validate_and_create(
            project=self.project,
            file_obj=SimpleUploadedFile(self.project_filename, b''))

        self.student_file = ag_models.ExpectedStudentFilePattern.objects.validate_and_create(
            pattern=self.submitted_filename,
            project=self.project)

        self.starter_args = {
            'name': 'steve',
            # 'student_resource_files': [self.submitted_filename],
            # 'test_resource_files': [self.project_filename],
            'project': self.project
        }


class InterpretedAGTestMiscTestCase(_SetUpBase, TemporaryFilesystemTestCase):
    def test_valid_init_with_defaults(self):
        test = ag_models.AutograderTestCaseFactory.validate_and_create(
            'interpreted_test_case',
            interpreter='python',
            entry_point_filename=self.project_filename,
            **self.starter_args)

        test.refresh_from_db()

        self.assertEqual('python', test.interpreter)
        self.assertEqual([], test.interpreter_flags)
        self.assertEqual(self.project_filename, test.entry_point_filename)

        self.assertEqual('interpreted_test_case', test.get_type_str())

    def test_valid_init_no_defaults(self):
        flags = ['spam', 'egg']
        test = ag_models.AutograderTestCaseFactory.validate_and_create(
            'interpreted_test_case',
            interpreter='python3',
            interpreter_flags=flags,
            entry_point_filename=self.project_filename,
            **self.starter_args)

        test.refresh_from_db()

        self.assertEqual('python3', test.interpreter)
        self.assertEqual(flags, test.interpreter_flags)
        self.assertEqual(self.project_filename, test.entry_point_filename)

        self.assertEqual('interpreted_test_case', test.get_type_str())

    def test_error_unsupported_interpreter(self):
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.AutograderTestCaseFactory.validate_and_create(
                'interpreted_test_case',
                interpreter='not_an_interpreter',
                entry_point_filename=self.project_filename,
                **self.starter_args)

        self.assertTrue('interpreter' in cm.exception.message_dict)

    def test_invalid_interpreter_flags(self):
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.AutograderTestCaseFactory.validate_and_create(
                'interpreted_test_case',
                interpreter='python',
                interpreter_flags=['good', 'bad; #><'],
                entry_point_filename=self.project_filename,
                **self.starter_args)

        self.assertTrue('interpreter_flags'in cm.exception.message_dict)

    def test_entry_point_filename_has_invalid_chars(self):
        with self.assertRaises(exceptions.ValidationError) as cm:
            ag_models.AutograderTestCaseFactory.validate_and_create(
                'interpreted_test_case',
                interpreter='python',
                entry_point_filename='../../waaaaa',
                **self.starter_args)

        self.assertTrue('entry_point_filename' in cm.exception.message_dict)


class RunInterpretedAutograderTestCaseTestCase(_SetUpBase, TemporaryFilesystemTestCase):
    def setUp(self):
        super().setUp()

        with open(self.project_file.abspath, 'w') as f:
            f.write(PyProgs.other_module)

        self.test = ag_models.AutograderTestCaseFactory.validate_and_create(
            'interpreted_test_case',
            interpreter='python3',
            entry_point_filename=self.project_filename,
            **self.starter_args)

        self.test.test_resource_files.add(self.project_file)
        self.test.student_resource_files.add(self.student_file)

        self.submission = ag_models.Submission.objects.validate_and_create(
            submission_group=self.group,
            submitted_files=[SimpleUploadedFile(self.submitted_filename, b'')])

        self.submitted_file_abspath = os.path.join(
            ut.get_submission_dir(self.submission), self.submitted_filename)

        self.sandbox = AutograderSandbox()
        self.sandbox.__enter__()

    def tearDown(self):
        super().tearDown()
        self.sandbox.__exit__()

    def test_zero_return_code_and_stdout(self):
        with open(self.submitted_file_abspath, 'w') as f:
            f.write(PyProgs.normal_exit)

        result = self.test.run(self.submission, self.sandbox)

        self.assertEqual(0, result.return_code)
        self.assertEqual('hello world\nwaluigi\n', result.standard_output)
        self.assertEqual('', result.standard_error_output)

    def test_nonzero_return_code_and_stderr(self):
        with open(self.submitted_file_abspath, 'w') as f:
            f.write(PyProgs.bad_exit)

        result = self.test.run(self.submission, self.sandbox)

        self.assertEqual(0, result.return_code)
        self.assertEqual('waluigi\n', result.standard_output)
        self.assertEqual('lulz\n', result.standard_error_output)

    def test_program_with_cmd_args(self):
        with open(self.submitted_file_abspath, 'w') as f:
            f.write(PyProgs.with_cmd_args)

        self.test.validate_and_update(
            command_line_arguments=['spam', 'egg', 'sausage'])
        result = self.test.run(self.submission, self.sandbox)
        self.assertEqual(0, result.return_code)
        expected_output = (self.project_filename + '\n' +
                           '\n'.join(self.test.command_line_arguments) +
                           '\nwaluigi\n')

        self.assertEqual(expected_output, result.standard_output)


class InterpretedAutograderTestCaseResourceLimitTestCase(_SetUpBase, TemporaryFilesystemTestCase):
    def setUp(self):
        super().setUp()

        self.interpreter = 'python3'
        self.stack_limit = random.randint(1000, 8000)
        self.virtual_mem_limit = random.randint(100000000, 200000000)
        self.process_limit = random.randint(1, 5)
        self.test = ag_models.AutograderTestCaseFactory.validate_and_create(
            'interpreted_test_case',
            interpreter=self.interpreter,
            entry_point_filename=self.project_filename,
            stack_size_limit=self.stack_limit,
            virtual_memory_limit=self.virtual_mem_limit,
            process_spawn_limit=self.process_limit,
            **self.starter_args)

    @mock.patch('autograder.security.autograder_sandbox.AutograderSandbox',
                autospec=True)
    def test_resource_limits_set(self, MockSandbox):
        sandbox = MockSandbox()
        self.test.run(None, sandbox)

        sandbox.run_command.assert_called_once_with(
            [self.interpreter, self.project_filename],
            input_content='',
            timeout=self.test.time_limit,
            max_num_processes=self.process_limit,
            max_stack_size=self.stack_limit,
            max_virtual_memory=self.virtual_mem_limit)


# -----------------------------------------------------------------------------


class PyProgs:
    normal_exit = """
print('hello world')
"""

    bad_exit = """
import sys
print('lulz', file=sys.stderr)
"""

    other_module = """
import my_file

print('waluigi')
"""

    with_cmd_args = """
import sys

for arg in sys.argv:
    print(arg)
"""
