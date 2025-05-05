# managerpanel/views.py
import csv
import io # For handling in-memory file for CSV decoding
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse, reverse_lazy # Import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden # For AJAX and access control
from .models import (
    CourseAssignment, ManagerProfile, Batch, Student, Cohort, Semester, Year
)
from .forms import ( # Import all forms from this app
    CourseAssignmentForm, BatchForm, StudentForm, StudentCSVUploadForm, StudentSearchForm
)
# Import necessary models and forms from responseupload
from responseupload.models import Course, Program
from responseupload.forms import (
    ProgramForm, CourseForm, SemesterForm, YearForm
)
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie # ensure_csrf_cookie might be useful for AJAX POST from JS Fetch
from django.views.decorators.http import require_POST # For status update and delete views
from django.contrib.auth.models import User
from django.conf import settings # Import settings if using for email
from django.core.mail import send_mail # Import send_mail if using for email
from django.db import transaction, IntegrityError # For atomic CSV upload and error handling
from django.db.models import Q, Prefetch, Count # For OR queries in search and prefetching
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger # For pagination
from django import forms # Import forms module

# ==============================================================================
# Helper Functions
# ==============================================================================

def is_manager(user):
    """
    Checks if the given user has a ManagerProfile associated with them
    and if the 'is_manager' flag is set to True.
    Also handles AnonymousUser gracefully.
    """
    if not user.is_authenticated:
        return False
    return ManagerProfile.objects.filter(user=user, is_manager=True).exists()

# ==============================================================================
# Manager Dashboard and Assignment Views
# ==============================================================================

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def manager_dashboard(request):
    """
    Displays the main dashboard for managers with action buttons and student search form.
    """
    student_search_form = StudentSearchForm(request.GET or None)
    context = {
        'student_search_form': student_search_form,
    }
    return render(request, 'managerpanel/manager_dashboard.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_course_assignment(request):
    """ Handles the creation of new course assignments by managers. """
    if request.method == 'POST':
        form = CourseAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Successfully assigned course {assignment.course.code}.')
            return redirect('managerpanel:list_assignments')
        else:
            error_list = '; '.join([f'{field}: {err[0]}' for field, err in form.errors.items()])
            messages.error(request, f'Error assigning course. Please correct: {error_list}')
    else:
        form = CourseAssignmentForm()
    context = {
        'form': form,
        'form_title': 'Assign New Course'
    }
    return render(request, 'managerpanel/create_course_assignment.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def edit_course_assignment(request, assignment_id):
    """ Handles the editing of an existing course assignment by managers. """
    assignment = get_object_or_404(CourseAssignment.objects.select_related('course', 'batch', 'semester', 'year'), pk=assignment_id)
    if request.method == 'POST':
        form = CourseAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Successfully updated assignment for {assignment.course.code}.')
            return redirect('managerpanel:list_assignments')
        else:
            error_list = '; '.join([f'{field}: {err[0]}' for field, err in form.errors.items()])
            messages.error(request, f'Error updating assignment. Please correct: {error_list}')
    else:
        form = CourseAssignmentForm(instance=assignment)
    context = {
        'form': form,
        'assignment': assignment,
        'form_title': f'Edit Assignment: {assignment.course.code} - {assignment.course.name}'
    }
    return render(request, 'managerpanel/edit_course_assignment.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
@require_POST
def delete_course_assignment(request, assignment_id):
     """ Handles the deletion of a course assignment by managers. """
     assignment = get_object_or_404(CourseAssignment.objects.select_related('course'), pk=assignment_id)
     course_code = assignment.course.code
     try:
         assignment.delete()
         messages.success(request, f'Successfully deleted assignment for {course_code}.')
     except Exception as e:
         messages.error(request, f"An error occurred while deleting assignment {course_code}: {e}")
     return redirect('managerpanel:list_assignments')

# ==============================================================================
# View for Listing Course Assignments
# ==============================================================================
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def list_course_assignments(request):
    """ Displays a list of all course assignments with pagination and filters. """
    assignment_list = CourseAssignment.objects.select_related(
        'course', 'course__program', 'batch', 'batch__cohort', 'semester', 'year'
    ).prefetch_related('faculty_members').all()

    # Filtering Logic
    course_query = request.GET.get('course_q', '').strip()
    faculty_query = request.GET.get('faculty_q', '').strip()
    batch_query = request.GET.get('batch_q', '').strip()
    semester_id = request.GET.get('semester', '')
    year_id = request.GET.get('year', '')

    if course_query: assignment_list = assignment_list.filter( Q(course__code__icontains=course_query) | Q(course__name__icontains=course_query) )
    if faculty_query: assignment_list = assignment_list.filter( Q(faculty_members__username__icontains=faculty_query) | Q(faculty_members__first_name__icontains=faculty_query) | Q(faculty_members__last_name__icontains=faculty_query) ).distinct()
    if batch_query: assignment_list = assignment_list.filter(batch__name__icontains=batch_query)
    if semester_id: assignment_list = assignment_list.filter(semester_id=semester_id)
    if year_id: assignment_list = assignment_list.filter(year_id=year_id)

    assignment_list = assignment_list.order_by('-year__name', '-semester__name', '-start_date', 'course__code')

    paginator = Paginator(assignment_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'assignments_page': page_obj,
        'course_query': course_query, 'faculty_query': faculty_query, 'batch_query': batch_query,
        'selected_semester_id': semester_id, 'selected_year_id': year_id,
        'available_semesters': Semester.objects.all().order_by('name'),
        'available_years': Year.objects.all().order_by('-name'),
    }
    return render(request, 'managerpanel/list_course_assignments.html', context)

# ==============================================================================
# Views for Creating Shared Components
# ==============================================================================

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
@csrf_protect
def handle_component_create_view(request, form_class, success_message, template_name, redirect_url_name):
    """Generic handler for creating simple component models."""
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            instance = form.save()
            messages.success(request, success_message)
            return redirect(redirect_url_name)
        else:
            error_list = '; '.join([f'{field}: {err[0]}' for field, err in form.errors.items()])
            messages.error(request, f'Error creating component. Please correct: {error_list}')
    else:
        form = form_class()
    model_name = getattr(form_class._meta.model._meta, 'verbose_name', form_class._meta.model.__name__)
    form_title = f"Create New {model_name}"
    return render(request, template_name, {'form': form, 'form_title': form_title})

# Specific views calling the handler
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_program_manager(request): return handle_component_create_view(request, ProgramForm, 'Program created successfully.', 'managerpanel/create_component.html', 'managerpanel:manager_dashboard')
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_semester_manager(request): return handle_component_create_view(request, SemesterForm, 'Semester created successfully.', 'managerpanel/create_component.html', 'managerpanel:manager_dashboard')
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_year_manager(request): return handle_component_create_view(request, YearForm, 'Year created successfully.', 'managerpanel/create_component.html', 'managerpanel:manager_dashboard')
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_course_manager(request): return handle_component_create_view(request, CourseForm, 'Course definition created successfully.', 'managerpanel/create_component.html', 'managerpanel:manager_dashboard')

# ==============================================================================
# Batch Management Views
# ==============================================================================

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def list_batches(request):
    """Lists all created batches."""
    batches = Batch.objects.select_related(
        'semester', 'cohort', 'program'
    ).prefetch_related(
        'students' # For student count display
    ).all().order_by('-year', 'status', 'semester__name', 'name')
    context = {'batches': batches}
    return render(request, 'managerpanel/list_batches.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def create_batch(request):
    """Handles creation of a new batch."""
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Batch "{form.cleaned_data["name"]}" created successfully.')
            return redirect('managerpanel:list_batches')
        else:
            error_list = '; '.join([f'{field}: {err[0]}' for field, err in form.errors.items()])
            messages.error(request, f'Error creating batch. Please correct: {error_list}')
    else:
        form = BatchForm()
    return render(request, 'managerpanel/create_or_edit_batch.html', {'form': form, 'form_title': 'Create New Batch'})

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def edit_batch(request, batch_id):
    """Handles editing of an existing batch."""
    batch = get_object_or_404(Batch.objects.select_related('cohort', 'semester', 'program'), pk=batch_id)
    if request.method == 'POST':
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            messages.success(request, f'Batch "{batch.name}" updated successfully.')
            return redirect('managerpanel:list_batches')
        else:
            error_list = '; '.join([f'{field}: {err[0]}' for field, err in form.errors.items()])
            messages.error(request, f'Error updating batch. Please correct: {error_list}')
    else:
        form = BatchForm(instance=batch)
    return render(request, 'managerpanel/create_or_edit_batch.html', {'form': form, 'batch': batch, 'form_title': f'Edit Batch: {batch.name}'})

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
@require_POST
def delete_batch(request, batch_id):
    """Handles deletion of a batch via POST."""
    batch = get_object_or_404(Batch.objects.prefetch_related('students'), pk=batch_id)
    student_count = batch.students.count()
    batch_name = batch.name
    try:
        batch.delete()
        messages.success(request, f'Batch "{batch_name}" and its {student_count} student(s) deleted.')
    except Exception as e:
        messages.error(request, f'Error deleting batch "{batch_name}": {e}. Check for linked Course Assignments.')
    return redirect('managerpanel:list_batches')


@require_POST
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def update_batch_status(request, batch_id):
    """Handles updating the status of a single batch via POST from the list view."""
    batch = get_object_or_404(Batch, pk=batch_id)
    new_status = request.POST.get('status')
    valid_statuses = [choice[0] for choice in Batch.BATCH_STATUS_CHOICES]
    if new_status in valid_statuses:
        if batch.status != new_status:
            batch.status = new_status
            batch.save(update_fields=['status'])
            messages.success(request, f'Status for batch "{batch.name}" updated to "{batch.get_status_display()}".')
    else:
        messages.error(request, f'Invalid status value submitted for batch "{batch.name}".')
    return redirect('managerpanel:list_batches')


@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def batch_detail(request, batch_id):
    """Displays the details of a specific batch and its students with pagination."""
    batch = get_object_or_404(Batch.objects.select_related('semester', 'cohort', 'program'), pk=batch_id)
    # Prefetch completed courses here for efficiency if displaying progress on this page
    student_list = batch.students.select_related(
        'enrollment_semester'
    ).prefetch_related(
        'completed_courses' # Prefetch for progress bar
    ).all().order_by('last_name', 'first_name')

    paginator = Paginator(student_list, 25)
    page_number = request.GET.get('page')
    students_page = paginator.get_page(page_number)
    context = {
        'batch': batch,
        'students_page': students_page,
    }
    return render(request, 'managerpanel/batch_detail.html', context)

# ==============================================================================
# Student Management Views
# ==============================================================================

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
#@ensure_csrf_cookie # May be needed if JS fetch doesn't automatically send cookie CSRF
def search_students(request):
    """
    Searches/Lists students based on query, status, cohort, program, and degree filters.
    """
    form = StudentSearchForm(request.GET or None)
    # Start with base queryset, including prefetches needed by template tags
    student_list = Student.objects.select_related(
        'batch', 'batch__cohort', 'batch__program', 'enrollment_semester'
    ).prefetch_related(
        'completed_courses' # Prefetch for progress bar tag
    ).all()

    # --- Filtering ---
    query = ''
    program_filter = None
    cohort_filter = None
    degree_filter = ''
    status_filter = ''
    results_found = True # Assume results initially

    if form.is_valid():
        query = form.cleaned_data.get('query','').strip()
        program_filter = form.cleaned_data.get('program')
        cohort_filter = form.cleaned_data.get('cohort')
        degree_filter = form.cleaned_data.get('degree', '').strip()
        status_filter = form.cleaned_data.get('status', '').strip()

        if query: student_list = student_list.filter( Q(student_id__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) )
        if program_filter: student_list = student_list.filter(batch__program=program_filter)
        if cohort_filter: student_list = student_list.filter(batch__cohort=cohort_filter)
        if degree_filter: student_list = student_list.filter(degree=degree_filter)
        if status_filter: student_list = student_list.filter(status=status_filter)
    # --- End Filtering ---

    student_list = student_list.order_by('batch__name', 'last_name', 'first_name')
    paginator = Paginator(student_list, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Check if results exist *after* filtering and pagination
    results_found = page_obj.object_list.exists() or not (query or program_filter or cohort_filter or degree_filter or status_filter)

    context = {
        'form': form,
        'students_page': page_obj,
        'query': query,
        'program_filter': program_filter.id if program_filter else '',
        'cohort_filter': cohort_filter.id if cohort_filter else '',
        'degree_filter': degree_filter,
        'status_filter': status_filter,
        'result_count': paginator.count,
        'results_found': results_found,
    }
    return render(request, 'managerpanel/search_students.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def add_student_manual(request, batch_id):
    """Handles manually adding a student to a specific batch."""
    batch = get_object_or_404(Batch.objects.select_related('program'), pk=batch_id)
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student_id = form.cleaned_data.get('student_id')
            email = form.cleaned_data.get('email')
            id_exists = Student.objects.filter(student_id=student_id).exists()
            email_exists = Student.objects.filter(email=email).exists()

            if id_exists: messages.error(request, f'Error: Student ID "{student_id}" already exists.')
            elif email_exists: messages.error(request, f'Error: Email "{email}" already exists.')
            else:
                try:
                    student = form.save(commit=False)
                    student.batch = batch
                    student.save()
                    form.save_m2m() # Important if StudentForm has M2M fields
                    messages.success(request, f'Student {student.first_name} {student.last_name} added to batch "{batch.name}".')
                    return redirect('managerpanel:batch_detail', batch_id=batch.id)
                except Exception as e: messages.error(request, f'An unexpected error occurred saving student: {e}')
        else:
             error_list = '; '.join([f'{field}: {err[0]}' for field, err in form.errors.items()])
             messages.error(request, f'Error adding student. Please correct: {error_list}')
    else:
        form = StudentForm(initial={'batch': batch})
        form.fields['batch'].widget = forms.HiddenInput()

    context = { 'form': form, 'batch': batch, 'form_title': f'Add Student to: {batch.name}'}
    return render(request, 'managerpanel/add_or_edit_student.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
def edit_student(request, student_id):
    """Handles editing an existing student's information."""
    student = get_object_or_404(Student.objects.select_related('batch'), pk=student_id)
    batch_id_for_redirect = student.batch.id if student.batch else None

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
             try:
                new_student_id = form.cleaned_data.get('student_id')
                new_email = form.cleaned_data.get('email')
                id_exists = Student.objects.filter(student_id=new_student_id).exclude(pk=student.pk).exists()
                email_exists = Student.objects.filter(email=new_email).exclude(pk=student.pk).exists()

                if id_exists: messages.error(request, f'Error: Student ID "{new_student_id}" already used.')
                elif email_exists: messages.error(request, f'Error: Email "{new_email}" already used.')
                else:
                    form.save()
                    messages.success(request, f'Student {student.first_name} {student.last_name} updated.')
                    # Redirect back smartly
                    redirect_url = request.POST.get('next', request.GET.get('next', None))
                    if redirect_url: return redirect(redirect_url)
                    if batch_id_for_redirect: return redirect('managerpanel:batch_detail', batch_id=batch_id_for_redirect)
                    return redirect('managerpanel:search_students')
             except Exception as e: messages.error(request, f'An unexpected error occurred saving student: {e}')
        else:
            error_list = '; '.join([f'{field}: {err[0]}' for field, err in form.errors.items()])
            messages.error(request, f'Error updating student. Please correct: {error_list}')
    else:
        form = StudentForm(instance=student)

    context = {
        'form': form, 'student': student, 'batch': student.batch,
        'form_title': f'Edit Student: {student.first_name} {student.last_name}'
    }
    return render(request, 'managerpanel/add_or_edit_student.html', context)

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
@require_POST
def delete_student(request, student_id):
    """Handles deletion of a student via POST."""
    student = get_object_or_404(Student.objects.select_related('batch'), pk=student_id)
    batch_id_for_redirect = student.batch.id if student.batch else None
    student_name = f"{student.first_name} {student.last_name}"
    try:
        student.delete()
        messages.success(request, f'Student "{student_name}" deleted.')
    except Exception as e:
        messages.error(request, f'Error deleting student "{student_name}": {e}')

    redirect_url = request.POST.get('next', request.GET.get('next', request.META.get('HTTP_REFERER', None)))
    if redirect_url: return redirect(redirect_url)
    if batch_id_for_redirect: return redirect('managerpanel:batch_detail', batch_id=batch_id_for_redirect)
    return redirect('managerpanel:search_students')

@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
@csrf_protect
def upload_students_csv(request):
    """Handles the upload and processing of a CSV file containing student data."""
    if request.method == 'POST':
        form = StudentCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            batch = form.cleaned_data['batch']
            csv_file = form.cleaned_data['csv_file']

            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Invalid file type: Please upload a .csv file.')
                return render(request, 'managerpanel/upload_students.html', {'form': form})

            try:
                decoded_file = io.TextIOWrapper(csv_file.file, encoding='utf-8-sig')
                reader = csv.DictReader(decoded_file)
                expected_headers = {'student_id', 'first_name', 'last_name', 'email', 'enrollment_semester', 'status'}
                optional_headers = {'phone_number', 'degree', 'notes'}

                if not reader.fieldnames:
                    messages.error(request, "CSV file is empty or has no header row.")
                    return render(request, 'managerpanel/upload_students.html', {'form': form})

                actual_headers = set(h.strip().lower() for h in reader.fieldnames if h)
                missing_required = expected_headers - actual_headers
                if missing_required:
                    messages.error(request, f"CSV missing required headers: {', '.join(sorted(list(missing_required)))}")
                    return render(request, 'managerpanel/upload_students.html', {'form': form})

                valid_semester_names = {s.name.lower(): s for s in Semester.objects.all()}
                valid_statuses = {s[0] for s in Student.STATUS_CHOICES}
                valid_degree_keys = {d[0] for d in Student.DEGREE_CHOICES}

                created_count, updated_count, errors, processed_ids = 0, 0, [], set()

                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):
                        row_data = {k.strip().lower(): v.strip() for k, v in row.items() if k and v is not None} # Ensure value isn't None
                        student_id = row_data.get('student_id')
                        first_name = row_data.get('first_name')
                        last_name = row_data.get('last_name')
                        email = row_data.get('email')
                        phone = row_data.get('phone_number')
                        enrollment_sem_name = row_data.get('enrollment_semester')
                        status = row_data.get('status', '').lower()
                        degree_key = row_data.get('degree', '').lower()
                        notes = row_data.get('notes')

                        row_errors = []
                        # Basic presence checks
                        if not student_id: row_errors.append("Missing student_id")
                        if not first_name: row_errors.append("Missing first_name")
                        if not last_name: row_errors.append("Missing last_name")
                        if not email: row_errors.append("Missing email")
                        if not enrollment_sem_name: row_errors.append("Missing enrollment_semester")
                        if not status: row_errors.append("Missing status")
                        # Value validation checks
                        if student_id and student_id in processed_ids: row_errors.append(f"Duplicate ID '{student_id}' in CSV.")
                        if status and status not in valid_statuses: row_errors.append(f"Invalid status '{row_data.get('status')}'. Valid: {', '.join(sorted(list(valid_statuses)))}.")
                        if degree_key and degree_key not in valid_degree_keys: row_errors.append(f"Invalid degree key '{row_data.get('degree')}'. Valid: {', '.join(sorted(list(valid_degree_keys)))}.")

                        enrollment_semester_obj = None
                        if enrollment_sem_name:
                             enrollment_semester_obj = valid_semester_names.get(enrollment_sem_name.lower())
                             if not enrollment_semester_obj: row_errors.append(f"Semester '{enrollment_sem_name}' not found.")

                        if row_errors:
                            errors.append(f"Row {row_num} (ID: {student_id or 'N/A'}): {'; '.join(row_errors)}")
                            processed_ids.add(student_id) # Add even if errored to prevent duplicate ID errors later
                            continue

                        student_data = {
                            'batch': batch, 'first_name': first_name, 'last_name': last_name, 'email': email,
                            'phone_number': phone or None, 'enrollment_semester': enrollment_semester_obj,
                            'status': status, 'degree': degree_key or None, 'notes': notes or None,
                        }
                        try:
                            student, created = Student.objects.update_or_create( student_id=student_id, defaults=student_data )
                            processed_ids.add(student_id)
                            if created: created_count += 1
                            else: updated_count += 1
                        except IntegrityError as e: errors.append(f"Row {row_num} (ID: {student_id}): DB error. Duplicate email?")
                        except Exception as e: errors.append(f"Row {row_num} (ID: {student_id}): Error - {e}")

                if errors:
                    for error in errors: messages.warning(request, error)
                    final_message = f"Upload processed: {len(errors)} error(s). Added: {created_count}, Updated: {updated_count}."
                    messages.error(request, final_message)
                else:
                    messages.success(request, f"CSV Upload successful for '{batch.name}'. Added: {created_count}, Updated: {updated_count}.")

                return redirect('managerpanel:batch_detail', batch_id=batch.id)

            except UnicodeDecodeError: messages.error(request, "Decoding error. Ensure CSV is UTF-8.")
            except KeyError as e: messages.error(request, f"CSV header error: Missing column {e}.")
            except Exception as e: messages.error(request, f"Unexpected error during processing: {e}")

            # Re-render form if exceptions occurred
            return render(request, 'managerpanel/upload_students.html', {'form': form})
        else:
            messages.error(request, "Invalid submission. Select batch and CSV file.")
            # Fall through to render GET request logic

    else: # GET Request
        form = StudentCSVUploadForm()
    return render(request, 'managerpanel/upload_students.html', {'form': form})


# ==============================================================================
# Student Progress View (Handles AJAX for inline editing)
# ==============================================================================

@require_POST
@login_required
@user_passes_test(is_manager, login_url=reverse_lazy('responseupload:login'))
@csrf_protect # Ensure CSRF validation
def update_single_course_status(request, student_id):
    """
    Handles AJAX POST request to add/remove a single completed course for a student.
    """
    student = get_object_or_404(Student.objects.select_related('batch__program'), pk=student_id)
    course_id_str = request.POST.get('course_id')
    is_completed_str = request.POST.get('is_completed')

    if not course_id_str or is_completed_str not in ['true', 'false']:
        return JsonResponse({'status': 'error', 'message': 'Missing or invalid parameters (course_id, is_completed).'}, status=400)

    try:
        course_id = int(course_id_str)
        is_completed = is_completed_str == 'true'
        course = get_object_or_404(Course, pk=course_id)

        # Verification: Ensure course belongs to the student's program
        if not student.batch or course.program != student.batch.program:
             return JsonResponse({'status': 'error', 'message': 'Course does not belong to student program.'}, status=400)

        if is_completed:
            student.completed_courses.add(course)
            action = "marked as completed"
        else:
            student.completed_courses.remove(course)
            action = "marked as pending"

        # Optionally recalculate and return progress data
        completed_count = student.completed_courses.count()
        total_courses = Course.objects.filter(program=student.batch.program).count()
        percentage = round((completed_count / total_courses * 100)) if total_courses > 0 else 0

        return JsonResponse({
            'status': 'success',
            'message': f'Course {course.code} {action} for {student}.',
            'completed_count': completed_count,
            'total_courses': total_courses,
            'percentage': percentage
        })

    except Course.DoesNotExist: return JsonResponse({'status': 'error', 'message': 'Course not found.'}, status=404)
    except ValueError: return JsonResponse({'status': 'error', 'message': 'Invalid course ID format.'}, status=400)
    except Exception as e:
        # Consider logging the error e
        print(f"Error updating progress: {e}") # Basic logging
        return JsonResponse({'status': 'error', 'message': 'An unexpected server error occurred.'}, status=500)