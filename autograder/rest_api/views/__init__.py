from .course_views.course_admins import CourseAdminViewSet
from .course_views.course_enrolled_students import CourseEnrolledStudentsViewSet
from .course_views.course_staff import CourseStaffViewSet

from .course_views.course_views import CourseViewSet

from .group_invitation_views.group_invitation_detail_view import GroupInvitationDetailViewSet
from .group_invitation_views.group_invitations_view import GroupInvitationsViewSet

from .group_views.group_detail_view import GroupDetailViewSet
from .group_views.groups_view import GroupsViewSet

from .oauth2callback import oauth2_callback

from .project_views.expected_student_file_pattern_views \
    .expected_student_file_pattern_detail_view import ExpectedStudentFilePatternDetailViewSet
from .project_views.expected_student_file_pattern_views\
    .expected_student_file_patterns_view import ExpectedStudentFilePatternsViewSet

from .project_views.project_detail_view import ProjectDetailViewSet
from .project_views.projects_view import ListCreateProjectView

from .project_views.uploaded_file_views.uploaded_file_detail_view import \
    UploadedFileDetailViewSet
from .project_views.uploaded_file_views.uploaded_files_view import UploadedFilesViewSet

from .project_views.project_detail_view import DownloadTaskDetailViewSet

from .submission_views.submission_detail_view import SubmissionDetailViewSet
from .submission_views.submissions_view import SubmissionsViewSet

from .user_views import UserViewSet

from .ag_test_views.ag_test_suite_views import (
    AGTestSuiteListCreateView, AGTestSuiteOrderView, AGTestSuiteDetailViewSet)
from .ag_test_views.ag_test_case_views import (
    AGTestCaseListCreateView, AGTestCaseOrderView, AGTestCaseDetailViewSet)
from .ag_test_views.ag_test_command_views import (
    AGTestCommandListCreateView, AGTestCommandOrderView, AGTestCommandDetailViewSet)

from .student_test_suite_views import (
    StudentTestSuiteListCreateView, StudentTestSuiteOrderView, StudentTestSuiteDetailViewSet)
