import csv
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from collections import Counter
from .forms import (
     ProgramForm, CourseForm, FacultyForm,
    CustomPasswordChangeForm, CourseSectionForm, SemesterForm, YearForm
)
from .models import (
    FacultyResponse, CourseResponse, Program, Course, Faculty,
    CourseSection, Semester, Year
)
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count
from datetime import datetime

# Home View
def home(request):
 return redirect('responseupload:login')

# Authentication Views

def user_login(request):
    """Handles user login using the standard AuthenticationForm."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Logged in successfully.')
                return HttpResponseRedirect(reverse('responseupload:dashboard'))
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid form submission.")
    else:
        form = AuthenticationForm(request)
    return render(request, 'responseupload/login.html', {'form': form})

def user_logout(request):
    """Logs out the user and redirects to the login page."""
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('responseupload:login')

# Dashboard View
@login_required
def dashboard(request):
    """Displays the main dashboard with charts and data summaries."""
    user = request.user

    # Get Faculty Responses for the user
    faculty_responses = FacultyResponse.objects.filter(faculty=user)

    # Get Course Responses for the user
    course_responses = CourseResponse.objects.filter(faculty=user)

    # Get unique courses from both response types
    faculty_courses = faculty_responses.values_list('course', flat=True).distinct()
    course_courses = course_responses.values_list('course', flat=True).distinct()

    # Combine the unique course IDs
    all_course_ids = set(faculty_courses) | set(course_courses)

    # Get the actual course objects
    user_courses = Course.objects.filter(id__in=all_course_ids)

    # Separate courses based on whether they have faculty or course responses
    faculty_response_courses = Course.objects.filter(id__in=faculty_courses)
    course_response_courses = Course.objects.filter(id__in=course_courses)

    # Create dictionaries to store response counts per course
    faculty_response_counts = {}
    for course_id in faculty_courses:
        count = faculty_responses.filter(course__id=course_id).count()
        faculty_response_counts[course_id] = count

    course_response_counts = {}
    for course_id in course_courses:
        count = course_responses.filter(course__id=course_id).count()
        course_response_counts[course_id] = count
     # Calculate years dynamically starting from 2024
    current_year = datetime.now().year
    year_range = list(range(2024, current_year + 1))

    context = {
        'user_courses': user_courses,
        'faculty_responses': faculty_responses,
        'course_responses': course_responses,
        'faculty_response_courses': faculty_response_courses,
        'course_response_courses': course_response_courses,
        'faculty_response_counts': faculty_response_counts,
        'course_response_counts': course_response_counts,
    }

    return render(request, 'responseupload/dashboard.html', context)

# Helper Function to Generate Chart Data

def get_chart_data(responses, question_field):
    """Generates chart data (labels and values) from response data."""
    labels = []
    values = []
    response_values = [getattr(response, question_field) for response in responses if getattr(response, question_field)]
    counts = Counter(response_values)
    for label, value in counts.items():
        labels.append(label)
        values.append(value)
    return labels, values

# Faculty and Course Response Views

@login_required
def view_faculty_responses(request):
    """Displays a list of faculty responses only for logged in user."""
    responses = FacultyResponse.objects.filter(faculty=request.user).order_by('course')
    return render(request, 'responseupload/faculty_response_list.html', {'responses': responses})

@login_required
def view_course_responses(request):
    """Displays a list of all course responses."""
    responses = CourseResponse.objects.filter(faculty=request.user).order_by('course')
    return render(request, 'responseupload/course_response_list.html', {'responses': responses})

# Password Change View

@login_required
def change_password(request):
    """Handles user password changes."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your password was successfully updated!')
            return redirect('responseupload:dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'responseupload/change_password.html', {'form': form})

# Create Views for Various Models (Using Admin for User Creation)

@login_required
def create_semester(request):
    """Creates a new semester."""
    return handle_create_view(request, SemesterForm, 'Semester created successfully.', 'responseupload/create_semester.html', request)

@login_required
def create_year(request):
    """Creates a new year."""
    return handle_create_view(request, YearForm, 'Year created successfully.', 'responseupload/create_year.html', request)

@login_required
def create_course_section(request):
    """Creates a new course section."""
    return handle_create_view(request, CourseSectionForm, 'Course section created successfully.', 'responseupload/create_course_section.html', request)

@login_required
def create_program(request):
    """Creates a new program."""
    return handle_create_view(request, ProgramForm, 'Program created successfully.', 'responseupload/create_program.html', request)

@login_required
def create_course(request):
    """Creates a new course."""
    return handle_create_view(request, CourseForm, 'Course created successfully.', 'responseupload/create_course.html', request)

@login_required
def create_faculty(request):
    """Creates a new faculty member."""
    return handle_create_view(request, FacultyForm, 'Faculty member created successfully.', 'responseupload/create_faculty.html', request)

# Generalized Create View Handler
@csrf_protect
def handle_create_view(request, form_class, success_message, template_name, ):
    """Handles the creation of new model instances using the provided form."""
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect('responseupload:dashboard')
    else:
        form = form_class()
    return render(request, template_name, {'form': form})

@login_required
def course_detail(request, course_id, user_id):
    course = get_object_or_404(Course, pk=course_id)
    user = get_object_or_404(User, pk=user_id)

    # Get faculty responses for this course and user
    faculty_responses = FacultyResponse.objects.filter(course=course, faculty=user)

    # Define the mapping of question fields to labels
    question_labels = {
        'q1': 'The organization of session materials and contents prepared by the instructor was-',
        'q2': 'Instructor\'s effort to make the concept clear to the class was-',
        'q3': 'The teaching learning methods (e.g., lecture, group work) followed by the instructor was-',
        'q4': 'The use of learning materials/ resources/ examples/ cases, etc. by the instructor was-',
        'q5': 'Instructor\'s effort to engage the students in learning was-',
        'q6': 'Instructor’s encouragement for the participation, discussion and questions from students was-',
        'q7': 'The guidance for assignment/class activity (group work, presentation, etc.) provided by the instructor was-',
        'q8': 'Instructor’s class time management was-',
    }

    # Prepare data for JavaScript
    chart_data = {}
    for i in range(1, 9):
        question_field = f'q{i}'
        data = faculty_responses.values(question_field).annotate(count=Count(question_field)).order_by(question_field)
        chart_data[question_field] = {
            'labels': [item[question_field] for item in data],
            'values': [item['count'] for item in data],
            'label': question_labels.get(question_field, f'Question {i}')  # Get label from mapping
        }

    # Get general comments for this course
    general_comments = faculty_responses.exclude(general_comments__isnull=True).exclude(general_comments__exact='').values_list('general_comments', flat=True)

    # Create a dictionary to store evaluation scores
    evaluation_scores = {
        'A: Excellent': 5,
        'B: Very Good': 4,
        'C: Good': 3,
        'D: Satisfactory': 2,
        'E: Not Satisfactory': 1,
    }

    # Calculate the average score for each question
    averages = {}
    total_score = 0
    total_respondents = faculty_responses.count()

    for i in range(1, 9):
        question_field = f'q{i}'
        question_responses = faculty_responses.values_list(question_field, flat=True)
        question_scores = [evaluation_scores.get(response, 0) for response in question_responses]
        average_score = sum(question_scores) / len(question_scores) if len(question_scores) > 0 else 0
        averages[question_field] = average_score
        total_score += average_score

    # Calculate the overall scores
    overall_total_out_of_40 = total_score
    overall_total_out_of_60 = (total_score / 40) * 60 if total_score > 0 else 0
    overall_average = total_score / 8 if total_score > 0 else 0

    context = {
        'course': course,
        'chart_data': json.dumps(chart_data),  # Convert data to JSON
        'general_comments': general_comments,
        'question_labels': question_labels,
        'averages': averages,
        'overall_total_out_of_40': overall_total_out_of_40,
        'overall_total_out_of_60': overall_total_out_of_60,
        'overall_average': overall_average,
        'total_respondents': total_respondents,
        'faculty_name': user.get_full_name()
    }

    return render(request, 'responseupload/course_detail.html', context)

@login_required
def course_response_detail(request, course_id, user_id):
    course = get_object_or_404(Course, pk=course_id)
    user = get_object_or_404(User, pk=user_id)

    course_responses = CourseResponse.objects.filter(course=course, faculty=user)

    # Define the mapping of question fields to labels for course responses
    question_labels = {
        'q1': 'The course provided an opportunity to develop relevant learning and competencies.',
        'q2': 'Textbooks/reading materials used in the course were appropriate.',
        'q3': 'Total time allocated for the course is appropriate to cover all the contents.',
        'q4': 'The contents specified in the syllabus for the course were covered.',
    }

    # Prepare data for charts
    chart_data = {}
    for i in range(1, 5):
        question_field = f'q{i}'
        data = course_responses.values(question_field).annotate(count=Count(question_field)).order_by(question_field)
        chart_data[question_field] = {
            'labels': [item[question_field] for item in data],
            'values': [item['count'] for item in data],
            'label': question_labels.get(question_field, f'Question {i}')
        }

    # Get general comments for this course
    general_comments = course_responses.exclude(general_comments__isnull=True).exclude(general_comments__exact='').values_list('general_comments', flat=True)

    # Evaluation scores mapping
    evaluation_scores = {
        'A: Strongly Agree': 5,
        'B: Agree': 4,
        'C: Neutral': 3,
        'D: Disagree': 2,
        'E: Strongly Disagree': 1,
    }

    # Calculate the average score for each question
    averages = {}
    total_score = 0
    total_respondents = course_responses.count()

    for i in range(1, 5):
        question_field = f'q{i}'
        question_responses = course_responses.values_list(question_field, flat=True)
        question_scores = [evaluation_scores.get(response, 0) for response in question_responses]
        average_score = sum(question_scores) / len(question_scores) if len(question_scores) > 0 else 0
        averages[question_field] = average_score
        total_score += average_score

    # Calculate the overall scores
    overall_total_out_of_20 = total_score  # Total score out of 20 (4 questions * max 5 points each)
    overall_total_out_of_60 = (total_score / 20) * 60 if total_score > 0 else 0  # Convert to out of 60
    overall_average = total_score / 4 if total_score > 0 else 0  # Average score

    context = {
        'course': course,
        'chart_data': json.dumps(chart_data),
        'general_comments': general_comments,
        'question_labels': question_labels,
        'averages': averages,
        'overall_total_out_of_20': overall_total_out_of_20,
        'overall_total_out_of_60': overall_total_out_of_60,
        'overall_average': overall_average,
        'total_respondents': total_respondents,
        'faculty_name': user.get_full_name()
    }

    return render(request, 'responseupload/course_response_detail.html', context)




