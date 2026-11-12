from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest
from django.db import transaction
from django.db.models import F
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_enrolled'] = check_if_enrolled(self.request.user, self.object)
        return context


@login_required
@require_POST
def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    with transaction.atomic():
        _, created = Enrollment.objects.get_or_create(user=request.user, course=course, defaults={'mode': 'honor'})
        if created:
            Course.objects.filter(pk=course.pk).update(total_enrollment=F('total_enrollment') + 1)
    return HttpResponseRedirect(reverse('onlinecourse:course_details', args=(course.id,)))


def extract_answers(request):
    values = [value for key in request.POST if key.startswith('choice') for value in request.POST.getlist(key)]
    return {int(value) for value in values}


@login_required
@require_POST
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    try:
        selected_ids = extract_answers(request)
    except (ValueError, TypeError):
        return HttpResponseBadRequest('Invalid choice identifier.')
    selected_choices = Choice.objects.filter(question__course=course, id__in=selected_ids)
    if selected_choices.count() != len(selected_ids):
        return HttpResponseBadRequest('A selected choice does not belong to this course.')
    with transaction.atomic():
        submission = Submission.objects.create(enrollment=enrollment)
        submission.choices.set(selected_choices)
    return HttpResponseRedirect(reverse('onlinecourse:exam_result', args=(course.id, submission.id)))


@login_required
def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id, enrollment__course=course, enrollment__user=request.user)
    selected_ids = set(submission.choices.values_list('id', flat=True))
    questions = course.question_set.prefetch_related('choice_set').all()
    total_points = sum(question.grade for question in questions)
    earned_points = sum(question.grade for question in questions if question.is_get_score(selected_ids))
    grade = round(100 * earned_points / total_points, 1) if total_points else 0
    context = {'course': course, 'submission': submission, 'choices': submission.choices.all(),
               'grade': grade, 'passed': total_points > 0 and grade >= 80,
               'earned_points': earned_points, 'total_points': total_points}
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
