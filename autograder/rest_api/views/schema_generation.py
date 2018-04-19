import functools
from collections import OrderedDict
from typing import Union, Type, List, get_type_hints, Tuple

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import fields
import django.contrib.postgres.fields as pg_fields
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.openapi import Schema, Parameter, Response
from sphinx.ext.autodoc import format_annotation

from timezone_field.fields import TimeZoneField

from autograder.core.models import AutograderModel
import autograder.core.models as ag_models
import autograder.core.fields as ag_fields
from autograder.core.models.ag_model_base import ToDictMixin
from autograder.rest_api.serializers.ag_model_serializer import AGModelSerializer

import autograder.handgrading.models as hg_models


AGModelType = Type[AutograderModel]
AGSerializableType = Type[ToDictMixin]
APIType = Union[AGModelType, AGSerializableType]

API_MODELS = OrderedDict([
    [ag_models.Course, 'Course'],
    [ag_models.Project, 'Project'],
    [ag_models.ExpectedStudentFilePattern, 'ExpectedStudentFilePattern'],
    [ag_models.UploadedFile, 'UploadedFile'],
    [ag_models.DownloadTask, 'DownloadTask'],
    [ag_models.SubmissionGroup, 'SubmissionGroup'],
    [ag_models.SubmissionGroupInvitation, 'SubmissionGroupInvitation'],
    [ag_models.Submission, 'Submission'],

    [ag_models.AGCommand, 'AGCommand'],

    [ag_models.AGTestSuite, 'AGTestSuite'],
    [ag_models.AGTestSuiteFeedbackConfig, 'AGTestSuiteFeedbackConfig'],
    [ag_models.AGTestCase, 'AGTestCase'],
    [ag_models.AGTestCaseFeedbackConfig, 'AGTestCaseFeedbackConfig'],
    [ag_models.AGTestCommand, 'AGTestCommand'],
    [ag_models.AGTestCommandFeedbackConfig, 'AGTestCommandFeedbackConfig'],

    [ag_models.AGTestSuiteResult.FeedbackCalculator, 'AGTestSuiteResult'],
    [ag_models.AGTestCaseResult.FeedbackCalculator, 'AGTestCaseResult'],
    [ag_models.AGTestCommandResult.FeedbackCalculator, 'AGTestCommandResult'],

    [ag_models.StudentTestSuite, 'StudentTestSuite'],
    [ag_models.StudentTestSuiteFeedbackConfig, 'StudentTestSuiteFeedbackConfig'],
    [ag_models.StudentTestSuiteResult.FeedbackCalculator, 'StudentTestSuiteResult'],

    [ag_models.RerunSubmissionsTask, 'RerunSubmissionsTask'],

    [hg_models.HandgradingRubric, 'HandgradingRubric'],
    [hg_models.Criterion, 'Criterion'],
    [hg_models.Annotation, 'Annotation'],
    [hg_models.HandgradingResult, 'HandgradingResult'],
    [hg_models.CriterionResult, 'CriterionResult'],
    [hg_models.AppliedAnnotation, 'AppliedAnnotation'],
    [hg_models.Comment, 'Comment'],
    [hg_models.Location, 'Location'],
])  # type: OrderedDict[APIType, str]


class AGSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request=request, public=public)
        ag_model_definitions = [
            (title, AGModelSchemaBuilder.get().get_schema(api_type))
            for api_type, title in API_MODELS.items()]
        schema.definitions.update(ag_model_definitions)
        return schema


# _TAGS_ORDER = [
#     'courses',
#
#     'projects',
#     'uploaded_files',
#     'expected_patterns',
#
#     'ag_test_suites',
#     'ag_test_cases',
#     'ag_test_commands',
#
#     'student_test_suites',
#
#     'group_invitations',
#     'groups',
#     'submission_groups',
#
#     'submissions',
#
#     'handgrading_rubrics',
#     'handgrading_rubric',
#
#     'criteria',
#     'annotations',
#
#     'criterion_results',
#     'applied_annotations',
#     'comments',
#
#     'download_tasks',
#     'rerun_submissions_tasks',
#
#     'users',
#     'logout',
# ]


class AGModelViewAutoSchema(SwaggerAutoSchema):
    def get_request_body_parameters(self, consumes):
        overrides = self.overrides.get('overrides', {})
        if 'request_body_parameters' in overrides:
            return overrides['request_body_parameters']

        serializer = self.get_request_serializer()
        if not isinstance(serializer, AGModelSerializer):
            return super().get_request_body_parameters(serializer)

        ag_model_class = serializer.ag_model_class  # type: APIType
        schema = AGModelSchemaBuilder.get().get_schema(ag_model_class)
        return list(
            field for field_name, field in schema.properties.items()
            if field_name in ag_model_class.get_editable_fields())

    def serializer_to_schema(self, serializer):
        if not isinstance(serializer, AGModelSerializer):
            return super().serializer_to_schema(serializer)

        ag_model_class = serializer.ag_model_class  # type: APIType
        return AGModelSchemaBuilder.get().get_schema(ag_model_class)


class NestedModelViewAutoSchema(AGModelViewAutoSchema):
    def get_tags(self, operation_keys):
        return [operation_keys[1]]


class AGModelSchemaBuilder:
    @staticmethod
    def get():
        if AGModelSchemaBuilder._instance is None:
            AGModelSchemaBuilder._instance = AGModelSchemaBuilder()

        return AGModelSchemaBuilder._instance

    _instance = None

    def __init__(self):
        self._schemas = {}

    def get_schema(self, api_type: APIType):
        if api_type not in self._schemas:
            self._schemas[api_type] = _build_schema(api_type)

        return self._schemas[api_type]


def _build_schema(api_class: APIType):
    title = API_MODELS[api_class]
    properties = OrderedDict()
    for field_name in api_class.get_serializable_fields():
        field = _get_field(field_name, api_class)
        properties[field_name] = _build_api_parameter(field, field_name)

    return Schema(title=title, type='object', properties=properties)


def _get_field(field_name: str, api_class: APIType):
    try:
        return api_class._meta.get_field(field_name)
    except (FieldDoesNotExist, AttributeError):
        return getattr(api_class, field_name)


@functools.singledispatch
def _build_api_parameter(field, field_name: str) -> Parameter:
    type_ = _get_django_field_type(field)
    description = field.help_text if hasattr(field, 'help_text') else ''
    try:
        required = not field.blank and field.default == fields.NOT_PROVIDED
    except AttributeError:
        required = False

    enum = None
    if type(field) == ag_fields.EnumField:
        enum = [item.value for item in field.enum_type]

    return Parameter(
        field_name, 'body',
        description=description,
        type=type_,
        required=required,
        enum=enum
    )


@_build_api_parameter.register(property)
def _(property_: property, field_name: str) -> Parameter:
    if field_name == 'pk':
        type_ = 'integer'
    else:
        type_ = get_type_hints(property_.fget).get('return', None)
        type_ = 'FIXME PROPERTY' if type_ is None else format_annotation(type_)
    description = property_.__doc__ if hasattr(property_, '__doc__') else ''

    return Parameter(
        field_name, 'body',
        description=description,
        type=type_,
    )


def _get_django_field_type(django_field) -> str:
    if type(django_field) in _FIELD_TYPES:
        return _FIELD_TYPES[type(django_field)]

    if type(django_field) == pg_fields.ArrayField:
        return 'List[{}]'.format(_get_django_field_type(django_field.base_field))

    model_class = django_field.model  # type: AGModelType
    field_name = django_field.name

    if django_field.is_relation:
        if django_field.many_to_many or django_field.one_to_many:
            if field_name in model_class.get_serialize_related_fields():
                return 'List[{}]'.format(API_MODELS[django_field.related_model])
            else:
                return 'List[integer]'

        if (field_name in model_class.get_serialize_related_fields() or
                field_name in model_class.get_transparent_to_one_fields()):
            return API_MODELS[django_field.related_model]
        else:
            return 'integer'

    return 'FIXME FIELD'


_FIELD_TYPES = {
    fields.IntegerField: 'integer',
    fields.BigIntegerField: 'integer',
    fields.FloatField: 'float',
    fields.BooleanField: 'bool',
    fields.NullBooleanField: 'Optional[bool]',
    fields.CharField: 'string',
    fields.TextField: 'string',
    fields.DateTimeField: 'datetime',
    fields.TimeField: 'time',

    TimeZoneField: 'timezone',

    pg_fields.JSONField: 'json',

    ag_fields.ShortStringField: 'string',
    ag_fields.StringArrayField: 'List[string]',
    ag_fields.EnumField: 'string'
}