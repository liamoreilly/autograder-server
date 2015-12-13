import os
import datetime
import json

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone

from autograder.models import (
    Project, Semester, Course, AutograderTestCaseBase)

import autograder.shared.utilities as ut

from autograder.tests.temporary_filesystem_test_case import (
    TemporaryFilesystemTestCase)

# note to self: ctor for SimpleUploadedFile takes (filename, contents).
#               contents must be binary data
from django.core.files.uploadedfile import SimpleUploadedFile


_FILENAME_WITH_SHELL_CHARS = '; echo "haxorz"; # '


class ProjectTestCase(TemporaryFilesystemTestCase):
    def setUp(self):
        super().setUp()
        self.course = Course.objects.validate_and_create(name='eecs280')
        self.semester = Semester.objects.validate_and_create(
            name='f15', course=self.course)
        self.PROJECT_NAME = 'stats_project'

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------

    def test_valid_create_with_defaults(self):
        new_project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)

        loaded_project = Project.objects.get(
            name=self.PROJECT_NAME, semester=self.semester)

        self.assertEqual(loaded_project, new_project)
        self.assertEqual(loaded_project.name, self.PROJECT_NAME)
        self.assertEqual(loaded_project.semester, self.semester)

        self.assertEqual(loaded_project.get_project_files(), [])
        self.assertEqual(loaded_project.visible_to_students, False)
        self.assertEqual(loaded_project.closing_time, None)
        self.assertEqual(loaded_project.disallow_student_submissions, False)
        self.assertEqual(
            loaded_project.allow_submissions_from_non_enrolled_students,
            False)
        self.assertEqual(loaded_project.min_group_size, 1)
        self.assertEqual(loaded_project.max_group_size, 1)
        self.assertEqual(loaded_project.required_student_files, [])
        self.assertEqual(loaded_project.expected_student_file_patterns, [])

    # -------------------------------------------------------------------------

    def test_valid_create_non_defaults(self):
        tomorrow_date = timezone.now() + datetime.timedelta(days=1)
        # print(tomorrow_date)
        min_group_size = 2
        max_group_size = 5
        required_student_files = ["spam.cpp", "eggs.cpp"]
        expected_student_file_patterns = [
            Project.FilePatternTuple("test_*.cpp", 1, 10),
            Project.FilePatternTuple("test[0-9].cpp", 2, 2),
            Project.FilePatternTuple("test[!0-9]?.cpp", 3, 5)
        ]

        new_project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME,
            semester=self.semester,
            visible_to_students=True,
            closing_time=tomorrow_date,
            disallow_student_submissions=True,
            allow_submissions_from_non_enrolled_students=True,
            min_group_size=min_group_size,
            max_group_size=max_group_size,
            required_student_files=required_student_files,
            expected_student_file_patterns=expected_student_file_patterns
        )

        new_project.validate_and_save()

        loaded_project = Project.objects.get(
            name=self.PROJECT_NAME, semester=self.semester)

        self.assertEqual(loaded_project, new_project)
        self.assertEqual(loaded_project.name, self.PROJECT_NAME)
        self.assertEqual(loaded_project.semester, self.semester)

        self.assertEqual(loaded_project.visible_to_students, True)
        self.assertEqual(loaded_project.closing_time, tomorrow_date)
        self.assertEqual(loaded_project.disallow_student_submissions, True)
        self.assertEqual(
            loaded_project.allow_submissions_from_non_enrolled_students,
            True)
        self.assertEqual(loaded_project.min_group_size, min_group_size)
        self.assertEqual(loaded_project.max_group_size, max_group_size)

        self.assertEqual(
            loaded_project.required_student_files, required_student_files)

        self.assertEqual(
            loaded_project.expected_student_file_patterns,
            expected_student_file_patterns)
        # iterable = zip(
        #     expected_student_file_patterns,
        #     sorted(loaded_project.get_expected_student_file_patterns()))

        # for expected, actual in iterable:
        #     self.assertEqual(expected[0], actual.pattern)
        #     self.assertEqual(expected[1], actual.min_num_matches)
        #     self.assertEqual(expected[2], actual.max_num_matches)

    # -------------------------------------------------------------------------

    def test_name_whitespace_stripped(self):
        Project.objects.validate_and_create(
            name='    ' + self.PROJECT_NAME + '    ', semester=self.semester)

        loaded_project = Project.objects.get(
            name=self.PROJECT_NAME, semester=self.semester)

        self.assertEqual(loaded_project.name, self.PROJECT_NAME)

    def test_exception_on_name_only_whitespace(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name='     ', semester=self.semester)
        self.assertTrue('name' in cm.exception.message_dict)

    def test_exception_on_empty_name(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name='', semester=self.semester)
        self.assertTrue('name' in cm.exception.message_dict)

    def test_exception_on_null_name(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=None, semester=self.semester)
        self.assertTrue('name' in cm.exception.message_dict)

    def test_exception_on_non_unique_name(self):
        Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)
        with self.assertRaises(ValidationError):
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester)

    # -------------------------------------------------------------------------

    def test_no_exception_same_name_different_semester(self):
        new_semester_name = 'w16'
        new_semester = Semester.objects.validate_and_create(
            name=new_semester_name, course=self.course)

        Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)

        new_project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=new_semester)

        loaded_new_project = Project.objects.get(
            name=self.PROJECT_NAME, semester=new_semester)

        self.assertEqual(loaded_new_project, new_project)
        self.assertEqual(loaded_new_project.name, new_project.name)
        self.assertEqual(loaded_new_project.semester, new_project.semester)

    def test_no_exception_same_semester_and_project_names_different_course(self):
        new_course_name = 'eecs381'
        new_course = Course.objects.validate_and_create(name=new_course_name)
        new_semester = Semester.objects.validate_and_create(
            name=self.semester.name, course=new_course)

        Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)
        new_project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=new_semester)

        loaded_new_project = Project.objects.get(
            name=self.PROJECT_NAME, semester=new_semester)

        self.assertEqual(loaded_new_project, new_project)
        self.assertEqual(loaded_new_project.name, new_project.name)
        self.assertEqual(loaded_new_project.semester, new_project.semester)

        self.assertNotEqual(
            loaded_new_project.semester.course, self.course)

    # -------------------------------------------------------------------------

    def test_exception_on_min_group_size_too_small(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                min_group_size=0)
        self.assertTrue('min_group_size' in cm.exception.message_dict)

    def test_exception_on_max_group_size_too_small(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                max_group_size=0)
        self.assertTrue('max_group_size' in cm.exception.message_dict)

    def test_exception_on_max_group_size_smaller_than_min_group_size(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                min_group_size=3, max_group_size=2)
        self.assertTrue('max_group_size' in cm.exception.message_dict)

    def test_exception_on_min_and_max_size_not_parseable_ints(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                min_group_size='spam', max_group_size='eggs')
        self.assertTrue('min_group_size' in cm.exception.message_dict)
        self.assertTrue('max_group_size' in cm.exception.message_dict)

    def test_no_exception_min_and_max_size_parseable_ints(self):
        Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester,
            min_group_size='1', max_group_size='2')

        loaded_project = Project.objects.get(
            name=self.PROJECT_NAME, semester=self.semester)
        self.assertEqual(loaded_project.min_group_size, 1)
        self.assertEqual(loaded_project.max_group_size, 2)

    # -------------------------------------------------------------------------

    def test_required_filename_whitespace_stripped(self):
        Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester,
            required_student_files=['   spam.cpp  ', 'eggs.cpp'])

        loaded_project = Project.objects.get(
            name=self.PROJECT_NAME, semester=self.semester)

        self.assertEqual(
            ['spam.cpp', 'eggs.cpp'], loaded_project.required_student_files)

    def test_exception_on_required_filename_is_only_whitespace(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                required_student_files=['spam.cpp', '     '])

        self.assertTrue('required_student_files' in cm.exception.message_dict)
        self.assertTrue(cm.exception.message_dict['required_student_files'][1])

    def test_exception_on_required_filename_is_empty_string(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                required_student_files=['spam.cpp', ''])

        self.assertTrue('required_student_files' in cm.exception.message_dict)

        # Make sure that there is an error message only in the correct spot.
        self.assertEqual(
            '', cm.exception.message_dict['required_student_files'][0])
        self.assertTrue(cm.exception.message_dict['required_student_files'][1])

    def test_exception_on_required_filename_has_illegal_path_chars(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                required_student_files=['..', '../spam.txt'])
        self.assertTrue(cm.exception.message_dict['required_student_files'][0])
        self.assertTrue(cm.exception.message_dict['required_student_files'][1])

    def test_exception_on_required_filename_has_illegal_shell_chars(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                required_student_files=[_FILENAME_WITH_SHELL_CHARS])
        self.assertTrue(cm.exception.message_dict['required_student_files'][0])

    def test_exception_on_required_filename_starts_with_dot(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                required_student_files=['.spamspam'])
        self.assertTrue(cm.exception.message_dict['required_student_files'][0])

    def test_exception_on_duplicate_required_filename(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                required_student_files=['spam.cpp', 'spam.cpp', 'eggs.cpp'])

        self.assertTrue(cm.exception.message_dict['required_student_files'][0])
        self.assertTrue(cm.exception.message_dict['required_student_files'][1])
        self.assertFalse(
            cm.exception.message_dict['required_student_files'][2])

    # -------------------------------------------------------------------------

    def test_pattern_whitespace_stripped(self):
        Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester,
            expected_student_file_patterns=[
                Project.FilePatternTuple("   eggs_*.txt    ", 1, 2)])

        loaded_project = Project.objects.get(
            name=self.PROJECT_NAME, semester=self.semester)
        self.assertEqual(
            [Project.FilePatternTuple("eggs_*.txt", 1, 2)],
            loaded_project.expected_student_file_patterns)

    def test_exception_on_pattern_is_only_whitespace(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                expected_student_file_patterns=[
                    Project.FilePatternTuple("       ", 1, 2)])

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)

        error_dicts = [
            json.loads(string) for string in
            cm.exception.message_dict['expected_student_file_patterns']]

        self.assertTrue(error_dicts[0])
        self.assertTrue(error_dicts[0]['pattern'])
        self.assertFalse(error_dicts[0]['min_num_matches'])
        self.assertFalse(error_dicts[0]['max_num_matches'])

    def test_no_exception_min_and_max_matches_are_parseable_ints(self):
        patterns = [Project.FilePatternTuple("eggs_*.txt", '1', '2')]

        Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester,
            expected_student_file_patterns=patterns)

        loaded_project = Project.objects.get(
            name=self.PROJECT_NAME, semester=self.semester)
        self.assertEqual(
            loaded_project.expected_student_file_patterns,
            [Project.FilePatternTuple("eggs_*.txt", 1, 2)])

    def test_exception_on_min_matches_not_integer(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                expected_student_file_patterns=[
                    Project.FilePatternTuple("eggs_*.txt", 'spam', 2)])

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)
        error_dict = json.loads(cm.exception.message_dict.get(
            'expected_student_file_patterns')[0])
        self.assertFalse(error_dict['pattern'])
        self.assertTrue(error_dict['min_num_matches'])
        self.assertFalse(error_dict['max_num_matches'])

    def test_exception_on_max_matches_not_integer(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                expected_student_file_patterns=[
                    Project.FilePatternTuple("eggs_*.txt", 1, 'spam')])

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)
        error_dict = json.loads(cm.exception.message_dict.get(
            'expected_student_file_patterns')[0])
        self.assertFalse(error_dict['pattern'])
        self.assertFalse(error_dict['min_num_matches'])
        self.assertTrue(error_dict['max_num_matches'])

    def test_exception_on_duplicate_expected_file_pattern(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                expected_student_file_patterns=[
                    Project.FilePatternTuple("eggs_*.txt", 1, 2),
                    Project.FilePatternTuple("eggs_*.txt", 1, 2),
                    Project.FilePatternTuple("spam_*.txt", 1, 2)])

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)
        error_dicts = [
            json.loads(string) for string in
            cm.exception.message_dict['expected_student_file_patterns']]

        self.assertTrue(error_dicts[0])

        self.assertTrue(error_dicts[0]['pattern'])
        self.assertFalse(error_dicts[0]['min_num_matches'])
        self.assertFalse(error_dicts[0]['max_num_matches'])

        self.assertTrue(error_dicts[1])
        self.assertTrue(error_dicts[1]['pattern'])
        self.assertFalse(error_dicts[1]['min_num_matches'])
        self.assertFalse(error_dicts[1]['max_num_matches'])

        self.assertFalse(error_dicts[2])

    def test_exception_on_negative_min_matches_in_expected_file_pattern(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                expected_student_file_patterns=[
                    Project.FilePatternTuple("eggs_*.txt", 1, 2),
                    Project.FilePatternTuple("spam_*.txt", -2, 4)])

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)
        error_dicts = [
            json.loads(string) for string in
            cm.exception.message_dict['expected_student_file_patterns']]

        self.assertFalse(error_dicts[0])

        self.assertTrue(error_dicts[1])
        self.assertFalse(error_dicts[1]['pattern'])
        self.assertTrue(error_dicts[1]['min_num_matches'])
        self.assertFalse(error_dicts[1]['max_num_matches'])

    def test_exception_on_negative_max_matches_in_expected_file_pattern(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                expected_student_file_patterns=[
                    Project.FilePatternTuple("spam_*.txt", 4, -2),
                    Project.FilePatternTuple("eggs_*.txt", 1, 2)])

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)

        error_dicts = [
            json.loads(string) for string in
            cm.exception.message_dict['expected_student_file_patterns']]

        self.assertTrue(error_dicts[0])
        self.assertFalse(error_dicts[0]['pattern'])
        self.assertFalse(error_dicts[0]['min_num_matches'])
        self.assertTrue(error_dicts[0]['max_num_matches'])

        self.assertFalse(error_dicts[1])

    def test_exception_on_max_less_than_min_in_expected_file_pattern(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                expected_student_file_patterns=[
                    Project.FilePatternTuple("spam_*.txt", 4, 1)])

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)

        error_dicts = [
            json.loads(string) for string in
            cm.exception.message_dict['expected_student_file_patterns']]

        self.assertTrue(error_dicts[0])
        self.assertFalse(error_dicts[0]['pattern'])
        self.assertFalse(error_dicts[0]['min_num_matches'])
        self.assertTrue(error_dicts[0]['max_num_matches'])

    def test_exception_on_expected_file_patterns_has_empty_string(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                expected_student_file_patterns=[
                    Project.FilePatternTuple("", 1, 2)])

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)

        error_dicts = [
            json.loads(string) for string in
            cm.exception.message_dict['expected_student_file_patterns']]

        self.assertTrue(error_dicts[0])
        self.assertTrue(error_dicts[0]['pattern'])
        self.assertFalse(error_dicts[0]['min_num_matches'])
        self.assertFalse(error_dicts[0]['max_num_matches'])

    def test_exception_on_expected_file_patterns_has_illegal_path_chars(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                expected_student_file_patterns=[
                    Project.FilePatternTuple("../test_*.cpp", 1, 2)])

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)

        error_dicts = [
            json.loads(string) for string in
            cm.exception.message_dict['expected_student_file_patterns']]

        self.assertTrue(error_dicts[0])
        self.assertTrue(error_dicts[0]['pattern'])
        self.assertFalse(error_dicts[0]['min_num_matches'])
        self.assertFalse(error_dicts[0]['max_num_matches'])

    def test_exception_on_expected_file_patterns_has_illegal_shell_chars(self):
        with self.assertRaises(ValidationError) as cm:
            Project.objects.validate_and_create(
                name=self.PROJECT_NAME, semester=self.semester,
                expected_student_file_patterns=[
                    Project.FilePatternTuple(
                        "spam[0-9]_; echo 'blah';", 1, 2)])

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)

        error_dicts = [
            json.loads(string) for string in
            cm.exception.message_dict['expected_student_file_patterns']]

        self.assertTrue(error_dicts[0])
        self.assertTrue(error_dicts[0]['pattern'])
        self.assertFalse(error_dicts[0]['min_num_matches'])
        self.assertFalse(error_dicts[0]['max_num_matches'])


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

class ProjectFilesystemTest(TemporaryFilesystemTestCase):
    def setUp(self):
        super().setUp()
        self.course = Course.objects.validate_and_create(name='eecs280')
        self.semester = Semester.objects.validate_and_create(
            name='f15', course=self.course)
        self.PROJECT_NAME = 'stats_project'

        self.sample_project_filename = "spam_EGGS-42.txt"
        self.sample_project_file_contents = b"spam egg sausage spam"
        self.sample_project_file = SimpleUploadedFile(
            self.sample_project_filename, self.sample_project_file_contents)

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------

    def test_project_root_dir_created_and_removed(self):
        project = Project(name=self.PROJECT_NAME, semester=self.semester)

        self.assertEqual(
            [],
            os.listdir(os.path.dirname(ut.get_project_root_dir(project))))

        project.save()

        expected_project_root_dir = ut.get_project_root_dir(project)

        self.assertTrue(os.path.isdir(expected_project_root_dir))

        project.delete()
        self.assertFalse(os.path.exists(expected_project_root_dir))

    # -------------------------------------------------------------------------

    def test_project_files_dir_created(self):
        project = Project(name=self.PROJECT_NAME, semester=self.semester)

        self.assertFalse(
            os.path.exists(
                os.path.dirname(ut.get_project_files_dir(project))))

        project.save()

        expected_project_files_dir = ut.get_project_files_dir(project)
        self.assertTrue(os.path.isdir(expected_project_files_dir))

    # -------------------------------------------------------------------------

    def test_project_submissions_dir_created(self):
        project = Project(name=self.PROJECT_NAME, semester=self.semester)

        self.assertFalse(
            os.path.exists(
                os.path.dirname(
                    ut.get_project_submission_groups_dir(project))))

        project.save()

        expected_project_submissions_by_student_dir = (
            ut.get_project_submission_groups_dir(project))

        self.assertTrue(
            os.path.isdir(expected_project_submissions_by_student_dir))

    # -------------------------------------------------------------------------

    def test_valid_add_project_file(self):
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)

        self.assertEqual(project.get_project_files(), [])

        project.add_project_file(self.sample_project_file)

        self.assertEqual(1, len(project.get_project_files()))
        uploaded_file = project.get_project_files()[0]

        self.assertEqual(
            os.path.basename(uploaded_file.name), self.sample_project_filename)
        self.assertEqual(
            uploaded_file.read(), self.sample_project_file_contents)

        with ut.ChangeDirectory(ut.get_project_files_dir(project)):
            self.assertTrue(os.path.isfile(self.sample_project_filename))

        file_retrieved_by_name = project.get_file(self.sample_project_filename)
        self.assertEqual(
            file_retrieved_by_name.read(), self.sample_project_file_contents)

        self.assertEqual(
            project.get_project_file_basenames(),
            [self.sample_project_filename])

    # -------------------------------------------------------------------------

    # This test can probably be phased out.
    # def test_exception_on_add_file_overwrite_not_ok(self):
    #     project = Project.objects.validate_and_create(
    #         name=self.PROJECT_NAME, semester=self.semester)

    #     project.add_project_file(
    #         self.sample_project_filename, self.sample_project_file_contents)

    #     with self.assertRaises(FileExistsError):
    #         project.add_project_file(
    #             self.sample_project_filename,
    #             self.sample_project_file_contents)

    # -------------------------------------------------------------------------

    # This test can probably be phased out.
#     def test_no_exception_on_add_file_overwrite_ok(self):
#         project = Project.objects.validate_and_create(
#             name=self.PROJECT_NAME, semester=self.semester)

#         self.assertEqual(project.project_files, [])

#         project.add_project_file(
#             self.sample_project_filename, self.sample_project_file_contents)

#         new_contents = "cheeeeeeeeese"
#         project.add_project_file(
#             self.sample_project_filename, new_contents, overwrite_ok=True)

#         with ut.ChangeDirectory(ut.get_project_files_dir(project)):
#             self.assertTrue(os.path.isfile(self.sample_project_filename))
#             with open(self.sample_project_filename) as f:
#                 self.assertEqual(new_contents, f.read())

#     # -------------------------------------------------------------------------

    # NOTE: Django's default storage system strips path information from
    # uploaded files
    def test_path_info_stripped_from_uploaded_filenames(self):
        # This test makes sure that add_project_file() doesn't allow
        # the user to add files in subdirectories (or worse, somewhere else
        # in the filesystem).
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)

        project.add_project_file(
            SimpleUploadedFile('../spam/egg/cheese.txt', b"haxorz!"))

        expected_name = os.path.join(
            ut.get_project_files_relative_dir(project), "cheese.txt")
        self.assertEqual(expected_name, project.get_project_files()[0].name)

    def test_exception_on_add_file_filename_is_dot_dot(self):
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)

        with self.assertRaises(ValidationError):
            project.add_project_file(
                SimpleUploadedFile('..', b"haxorz!"))

    def test_exception_on_filename_that_has_shell_characters(self):
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)
        with self.assertRaises(ValidationError):
            project.add_project_file(
                SimpleUploadedFile(_FILENAME_WITH_SHELL_CHARS, b"haxorz!"))

    def test_exception_on_filename_that_starts_with_dot(self):
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)
        with self.assertRaises(ValidationError):
            project.add_project_file(
                SimpleUploadedFile('.cheese.txt', b"whoa!"))

    def test_exception_on_empty_filename(self):
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)
        with self.assertRaises(ValidationError):
            project.add_project_file(
                SimpleUploadedFile("", self.sample_project_file_contents))

    # -------------------------------------------------------------------------

    def test_valid_remove_project_file(self):
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)
        project.add_project_file(self.sample_project_file)

        with ut.ChangeDirectory(ut.get_project_files_dir(project)):
            self.assertTrue(os.path.isfile(self.sample_project_filename))

        project.remove_project_file(self.sample_project_filename)
        with ut.ChangeDirectory(ut.get_project_files_dir(project)):
            self.assertFalse(os.path.isfile(self.sample_project_filename))

    def test_exception_on_remove_nonexistant_project_file(self):
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)
        with self.assertRaises(ObjectDoesNotExist):
            project.remove_project_file(self.sample_project_filename)

    def test_exception_on_remove_project_file_test_depends_on(self):
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester)
        project.add_project_file(self.sample_project_file)

        AutograderTestCaseBase.objects.validate_and_create(
            name='testy', project=project,
            test_resource_files=[self.sample_project_filename])

        with self.assertRaises(ValidationError):
            project.remove_project_file(self.sample_project_filename)

    import unittest
    @unittest.skip('todo')
    def test_exception_on_remove_project_file_suite_depends_on(self):
        self.fail()

    def test_exception_on_remove_student_file_test_depends_on(self):
        filename = 'required.cpp'
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester,
            required_student_files=[filename])

        AutograderTestCaseBase.objects.validate_and_create(
            name='testy', project=project,
            student_resource_files=[filename])

        with self.assertRaises(ValidationError) as cm:
            project.required_student_files = []

        self.assertTrue('required_student_files' in cm.exception.message_dict)

    def test_exception_on_remove_student_files_multiple_tests_depend_on(self):
        filenames = ['required1.cpp', 'required2.cpp', 'required3.cpp']
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester,
            required_student_files=filenames)

        tests = []
        for file_, index in zip(filenames, range(len(filenames))):
            tests.append(AutograderTestCaseBase.objects.validate_and_create(
                name='testy{}'.format(index), project=project,
                student_resource_files=[file_]))

        with self.assertRaises(ValidationError) as cm:
            project.required_student_files = []

        self.assertTrue('required_student_files' in cm.exception.message_dict)

    @unittest.skip('needs student test suite functionality')
    def test_exception_on_remove_student_file_suite_depends_on(self):
        self.fail()

    @unittest.skip('needs student test suite functionality')
    def test_exception_on_remove_student_files_multiple_suites_depend_on(self):
        self.fail()

    def test_exception_on_remove_student_pattern_test_depends_on(self):
        pattern = Project.FilePatternTuple('test_*.cpp', 0, 3)
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester,
            expected_student_file_patterns=[pattern])

        AutograderTestCaseBase.objects.validate_and_create(
            name='testy', project=project,
            student_resource_files=[pattern.pattern])

        with self.assertRaises(ValidationError) as cm:
            project.expected_student_file_patterns = []

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)

    def test_exception_on_remove_patterns_multiple_tests_depend_on(self):
        patterns = [
            Project.FilePatternTuple('test_*.cpp', 0, 3),
            Project.FilePatternTuple('fily_*.cpp', 0, 3),
            Project.FilePatternTuple('wabbit_*.cpp', 0, 3)
        ]
        project = Project.objects.validate_and_create(
            name=self.PROJECT_NAME, semester=self.semester,
            expected_student_file_patterns=patterns)

        tests = []
        for file_, index in zip(patterns, range(len(patterns))):
            tests.append(AutograderTestCaseBase.objects.validate_and_create(
                name='testy{}'.format(index), project=project,
                student_resource_files=[
                    pat_obj.pattern for pat_obj in patterns]))

        with self.assertRaises(ValidationError) as cm:
            project.expected_student_file_patterns = []

        self.assertTrue(
            'expected_student_file_patterns' in cm.exception.message_dict)

    @unittest.skip('todo')
    def test_exception_on_remove_pattern_suite_depends_on(self):
        self.fail()

    @unittest.skip('todo')
    def test_exception_on_remove_multiple_patterns_suites_depend_on(self):
        self.fail()
