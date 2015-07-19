import os
import json
import traceback

from django.views.generic.base import View
from django.views.generic.edit import CreateView, DeleteView

from django.core.exceptions import ValidationError
from django.forms.forms import NON_FIELD_ERRORS

from django.shortcuts import get_object_or_404, render

from django.template import RequestContext
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponse, HttpResponseRedirect

# from django.views.decorators.csrf import ensure_csrf_cookie
# from django.utils.decorators import method_decorator

from autograder.models import Course, Semester, Project


class ExceptionLoggingView(View):
    """
    View base class that catches any exceptions thrown from dispatch(),
    prints them to the console, and then rethrows.
    """
    def dispatch(self, *args, **kwargs):
        try:
            return super().dispatch(*args, **kwargs)
        except Exception:
            traceback.print_exc()
            raise


class AllCoursesView(CreateView):
    template_name = 'autograder/course_list.html'
    model = Course
    fields = ['name']
    success_url = reverse_lazy('course-list')

    def get_courses_to_display(self):
        # TODO: Check and filter based on permissions/enrollment
        return Course.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = self.get_courses_to_display()
        return context


class DeleteCourse(DeleteView):
    model = Course
    context_object_name = 'course'
    success_url = reverse_lazy('course-list')
    template_name = 'autograder/delete_course.html'


class SingleCourseView(ExceptionLoggingView):
    TEMPLATE_NAME = 'autograder/course_detail.html'

    def get(self, request, course_name):
        """
        View a Course and the Semesters that belong to it.
        """
        return render(request, SingleCourseView.TEMPLATE_NAME,
                      self.get_context_starter(course_name))

    def post(self, request, course_name):
        """
        Add a new Semester to the Course.
        """
        try:
            # TODO: csrf check
            Semester.objects.validate_and_create(
                name=request.POST['semester_name'],
                course=self.get_course(course_name))

            success_url = reverse_lazy('course-detail', args=[course_name])
            return HttpResponseRedirect(success_url)
        except ValidationError as e:
            context = self.get_context_starter(course_name)
            context['request'] = request.POST
            context['errors'] = e.message_dict
            print(context['errors'])
            context['non_field_errors'] = e.message_dict.get(
                NON_FIELD_ERRORS, {})

            context = RequestContext(self.request, context)
            return render(request, SingleCourseView.TEMPLATE_NAME, context)

    def get_course(self, course_name):
        return get_object_or_404(Course, name=course_name)

    def get_semesters_to_display(self, course):
        # TODO: Check and filter based on permissions/enrollment
        self.semesters_to_display = course.semesters.all()
        return self.semesters_to_display

    def get_context_starter(self, course_name):
        course = self.get_course(course_name)
        return {
            'course': course,
            'semesters': self.get_semesters_to_display(course),
            'errors': {},
            'non_field_errors': {}
        }


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def _get_semester(course_name, semester_name):
    return get_object_or_404(
        Semester, name=semester_name, course__name=course_name)


class DeleteSemester(ExceptionLoggingView):
    TEMPLATE_NAME = 'autograder/delete_semester.html'

    def get(self, request, course_name, semester_name):
        semester = _get_semester(course_name, semester_name)
        return render(
            request, DeleteSemester.TEMPLATE_NAME,
            RequestContext(request, {'semester': semester}))

    def post(self, request, course_name, semester_name):
        # TODO: csrf check
        semester = _get_semester(course_name, semester_name)
        semester.delete()
        return HttpResponseRedirect(
            reverse_lazy('course-detail', args=[course_name]))


class SemesterView(ExceptionLoggingView):
    TEMPLATE_NAME = 'autograder/semester_detail.html'

    def get(self, request, course_name, semester_name):
        """
        View a Semester and Projects that belong to it.
        """
        context = self.get_context_starter(course_name, semester_name)
        return render(request, SemesterView.TEMPLATE_NAME, context)

    def post(self, request, course_name, semester_name):
        try:
            # TODO: csrf
            Project.objects.validate_and_create(
                name=request.POST['project_name'],
                semester=_get_semester(course_name, semester_name))

            success_url = reverse_lazy(
                'semester-detail', args=[course_name, semester_name])
            return HttpResponseRedirect(success_url)
        except ValidationError as e:
            context = self.get_context_starter(course_name, semester_name)
            context['request'] = request.POST
            context['errors'] = e.message_dict
            context['non_field_errors'] = e.message_dict.get(
                NON_FIELD_ERRORS, {})
            context = RequestContext(self.request, context)
            return render(request, SemesterView.TEMPLATE_NAME, context)

    def get_context_starter(self, course_name, semester_name):
        semester = _get_semester(course_name, semester_name)
        return {
            'course': semester.course,
            'semester': semester,
            'projects': semester.projects.all(),
            'errors': {},
            'non_field_errors': {}
        }


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def _get_project(course_name, semester_name, project_name):
    semester = _get_semester(course_name, semester_name)
    return get_object_or_404(
        Project, name=project_name, semester=semester)


class DeleteProject(ExceptionLoggingView):
    TEMPLATE_NAME = 'autograder/delete_project.html'

    def get(self, request, course_name, semester_name, project_name):
        project = _get_project(course_name, semester_name, project_name)
        return render(
            request, DeleteProject.TEMPLATE_NAME,
            RequestContext(request, {'project': project}))

    def post(self, request, course_name, semester_name, project_name):
        # TODO: csrf
        project = _get_project(course_name, semester_name, project_name)
        print(project.name)
        project.delete()
        return HttpResponseRedirect(
            reverse_lazy('semester-detail', args=[course_name, semester_name]))


class ProjectView(ExceptionLoggingView):
    TEMPLATE_NAME = 'autograder/project_detail.html'

    def get(self, request, course_name, semester_name, project_name):
        return render(
            request, ProjectView.TEMPLATE_NAME,
            self.get_context_starter(course_name, semester_name, project_name))

    # def post(self, request, course_name, semester_name, project_name):
    #     pass

    def get_context_starter(self, course_name, semester_name, project_name):
        project = _get_project(course_name, semester_name, project_name)
        return {
            'course': project.semester.course,
            'semester': project.semester,
            'project': project,
            'autograder_test_cases': project.autograder_test_cases.all(),
            'errors': {},
            'non_field_errors': {}
        }


class AddProjectFile(ExceptionLoggingView):
    # @method_decorator(ensure_csrf_cookie)
    # def dispatch(self, *args, **kwargs):
    #     return super().dispatch(*args, **kwargs)

    def get(self, request, course_name, semester_name, project_name):
        """
        Returns a list of available files.
        """
        project = _get_project(course_name, semester_name, project_name)
        files = project.get_project_files()

        response = {'files': []}
        for field_file in files:
            name = os.path.basename(field_file.name)
            response['files'].append({
                'name': name,
                'size': field_file.size,
                'url': reverse('view-project-file',
                               args=[course_name, semester_name,
                                     project_name, name]),
                'deleteUrl': reverse('delete-project-file',
                                     args=[course_name, semester_name,
                                           project_name, name]),
                'deleteType': 'POST'
            })

        return HttpResponse(json.dumps(response), content_type='text/json')

    def post(self, request, course_name, semester_name, project_name):
        project = _get_project(course_name, semester_name, project_name)
        # The request.FILES container is a dictionary-like data structure
        # that is part of django and undocumented. As a workaround until
        # we figure out how to accomplish the same iteration with that
        # structure, we can construct a regular dictionary out of it
        # and then proceed normally.
        files = dict(request.FILES).get('files')

        response = {'files': []}

        for file_obj in files:
            data = {
                'name': file_obj.name,
                'size': file_obj.size
            }
            try:
                project.add_project_file(file_obj)
                url_args = [
                    course_name, semester_name, project_name, file_obj.name]
                data['url'] = reverse('view-project-file', args=url_args)
                data['deleteUrl'] = reverse(
                    'delete-project-file', args=url_args)
                data['deleteType'] = 'POST'
            except ValidationError as e:
                data['error'] = e.message_dict['uploaded_file'][0]

            response['files'].append(data)

        return HttpResponse(json.dumps(response), content_type='text/json')


class ViewProjectFile(ExceptionLoggingView):
    def get(self, request, course_name, semester_name, project_name, filename):
        project = _get_project(course_name, semester_name, project_name)
        file_obj = project.get_file(filename)
        file_obj.open()

        # TODO: send large files in chunks
        return HttpResponse(
            file_obj.read().decode('utf-8'), content_type='text/plain')


class DeleteProjectFile(ExceptionLoggingView):
    def post(self, request, course_name, semester_name,
             project_name, filename):
        print('boo')
        try:
            project = _get_project(course_name, semester_name, project_name)
            project.remove_project_file(filename)
            return HttpResponse(
                json.dumps({'files': [{filename: True}]}),
                content_type='text/json')

        except Exception:
            return HttpResponse(
                json.dumps({'files': [{filename: False}]}),
                content_type='text/json')
