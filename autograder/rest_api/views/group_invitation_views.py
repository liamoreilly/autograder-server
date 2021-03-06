import itertools

from django.contrib.auth.models import User
from django.db import transaction
from django.utils.decorators import method_decorator
from drf_composable_permissions.p import P
from rest_framework import exceptions, mixins, permissions, response, status
from rest_framework.decorators import action

import autograder.core.models as ag_models
import autograder.rest_api.permissions as ag_permissions
import autograder.utils.testing as test_ut
from autograder import utils
from autograder.rest_api.schema import (AGDetailViewSchemaGenerator, AGListViewSchemaMixin,
                                        APITags, CustomViewSchema, as_content_obj)
from autograder.rest_api.views.ag_model_views import (AGModelAPIView, AGModelDetailView,
                                                      NestedModelView,
                                                      convert_django_validation_error,
                                                      require_body_params)


class CanSendInvitation(permissions.BasePermission):
    def has_object_permission(self, request, view, project: ag_models.Project):
        if (project.disallow_group_registration
                and not project.course.is_staff(request.user)):
            return False

        if (project.course.is_handgrader(request.user)
                and not project.course.is_student(request.user)
                and not project.course.is_staff(request.user)):
            return False

        return True


list_create_invitation_permissions = (
    # Only staff can list invitations.
    (P(ag_permissions.IsReadOnly)) & P(ag_permissions.is_staff())
    | (~P(ag_permissions.IsReadOnly) & P(ag_permissions.can_view_project()) & P(CanSendInvitation))
)


class _ListCreateInvitationSchema(AGListViewSchemaMixin, CustomViewSchema):
    pass


class ListCreateGroupInvitationView(NestedModelView):
    schema = _ListCreateInvitationSchema(
        [APITags.group_invitations],
        api_class=ag_models.GroupInvitation,
        data={
            'POST': {
                'operation_id': 'createGroupInvitation',
                'request': {
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'recipient_usernames': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'string',
                                            'format': 'username'
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                'responses': {
                    '201': {
                        'content': as_content_obj(ag_models.GroupInvitation)
                    }
                }
            }
        }
    )

    permission_classes = [list_create_invitation_permissions]

    model_manager = ag_models.Project.objects
    nested_field_name = 'group_invitations'
    parent_obj_field_name = 'project'

    def get(self, *args, **kwargs):
        return self.do_list()

    @method_decorator(require_body_params('recipient_usernames'))
    @transaction.atomic()
    @convert_django_validation_error
    def post(self, *args, **kwargs):
        project = self.get_object()
        for key in self.request.data:
            if key != 'recipient_usernames':
                raise exceptions.ValidationError({'invalid_fields': [key]})

        recipients = [
            User.objects.get_or_create(username=username)[0]
            for username in self.request.data.pop('recipient_usernames')]

        utils.lock_users(itertools.chain([self.request.user], recipients))

        invitation = ag_models.GroupInvitation.objects.validate_and_create(
            self.request.user,
            recipients,
            project=project,
        )
        return response.Response(self.serialize_object(invitation), status.HTTP_201_CREATED)


class CanReadOrEditInvitation(permissions.BasePermission):
    def has_object_permission(self, request, view, invitation):
        is_staff = invitation.project.course.is_staff(request.user)
        is_involved = (request.user == invitation.sender
                       or request.user in invitation.recipients.all())

        if request.method.lower() == 'get':
            return is_staff or is_involved

        if invitation.project.disallow_group_registration and not is_staff:
            return False

        return is_involved


invitation_detail_permissions = (
    P(ag_permissions.can_view_project()) & P(CanReadOrEditInvitation)
)


class GroupInvitationDetailView(AGModelDetailView):
    schema = AGDetailViewSchemaGenerator([APITags.group_invitations])

    permission_classes = [invitation_detail_permissions]
    model_manager = ag_models.GroupInvitation.objects

    def get(self, *args, **kwargs):
        return self.do_get()

    def delete(self, *args, **kwargs):
        """
        Revoke or reject this invitation.
        """
        return self.do_delete()


class AcceptGroupInvitationView(AGModelAPIView):
    schema = CustomViewSchema([APITags.group_invitations], {
        'POST': {
            'operation_id': 'acceptGroupInvitation',
            'responses': {
                '200': {
                    'description': 'You have accepted the invitation.',
                    'content': as_content_obj(ag_models.GroupInvitation)
                },
                '201': {
                    'description': 'All invited users have accepted the invitation.',
                    'content': as_content_obj(ag_models.Group)
                }
            }
        }
    })

    model_manager = ag_models.GroupInvitation.objects
    permission_classes = [invitation_detail_permissions]

    @convert_django_validation_error
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        """
        Accept this group invitation. If all recipients have accepted,
        create a group, delete the invitation, and return the group.
        """
        invitation = self.get_object()
        invitation.recipient_accept(request.user)
        if not invitation.all_recipients_accepted:
            return response.Response(invitation.to_dict())

        members = [invitation.sender] + list(invitation.recipients.all())
        utils.lock_users(members)
        # Keep this hook just after the users are locked
        test_ut.mocking_hook()

        group = ag_models.Group.objects.validate_and_create(members, project=invitation.project)

        invitation.delete()
        return response.Response(group.to_dict(), status=status.HTTP_201_CREATED)
