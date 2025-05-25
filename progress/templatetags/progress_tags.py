# progress/templatetags/progress_tags.py
# ... (imports remain the same) ...
from django import template
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from responseupload.models import Course, Semester, Year
from managerpanel.models import Student, CourseAssignment, Batch
import math

register = template.Library()

@register.simple_tag(takes_context=True)
def student_progress_cell(context, student):
    # ... (validation and data fetching remain the same) ...
    if not isinstance(student, Student): return mark_safe('<small class="text-muted">Invalid Student</small>')
    if not student.batch: return mark_safe('<small class="text-muted">No Batch Assigned</small>')
    if not student.batch.program: return mark_safe('<small class="text-muted">Batch has No Program</small>')
    program = student.batch.program
    required_courses = Course.objects.filter(program=program).order_by('code')
    if not required_courses.exists(): return mark_safe('<small class="text-muted">No Courses in Program</small>')
    total_courses = required_courses.count()
    completed_course_ids = set(student.completed_courses.values_list('id', flat=True))
    completed_count = len(completed_course_ids)
    assignment_info = {}
    if completed_course_ids:
        student_assignments = CourseAssignment.objects.filter(batch=student.batch, course_id__in=completed_course_ids).select_related('semester', 'year').order_by('course_id', '-year__name', '-semester__name')
        for ca in student_assignments:
            if ca.course_id not in assignment_info: assignment_info[ca.course_id] = {'semester': ca.semester.name if ca.semester else '?', 'year': str(ca.year.name) if ca.year else '?'}

    # --- Part 1: Generate Read-Only Progress Bar HTML ---
    bar_items_html = ""
    segment_width_float = 100 / total_courses if total_courses > 0 else 0
    for i, course in enumerate(required_courses):
        is_completed = course.id in completed_course_ids
        status_class = "bg-success" if is_completed else "bg-danger"
        tooltip_text = f"{course.code} - {course.name}"
        if is_completed: info = assignment_info.get(course.id); tooltip_text += f" (Completed{': ' + info['semester'] + ' ' + info['year'] if info else ''})"
        else: tooltip_text += f" (Pending)"
        current_width = segment_width_float
        if i == total_courses - 1: current_width = 100 - (segment_width_float * (total_courses - 1))
        current_width = max(0, min(100, current_width)); formatted_width = f"{current_width:.2f}"

        # --- ADD data-course-id to the read-only bar segment ---
        bar_items_html += format_html(
            '<div class="progress-bar {status_class}" role="progressbar" style="width: {width}%" '
            'data-bs-toggle="tooltip" data-bs-placement="top" title="{tooltip}" data-course-id="{course_id}">' # Added data-course-id
            '{code}'
            '</div>',
            status_class=status_class, width=formatted_width,
            tooltip=tooltip_text, code=course.code, course_id=course.id # Pass course.id
        )
        # --- END ADD ---

    progress_bar_html = format_html('<div class="progress" style="height: 18px;">{}</div>', mark_safe(bar_items_html))
    percentage_float = (completed_count / total_courses * 100) if total_courses > 0 else 0
    formatted_percentage = f"{percentage_float:.0f}"
    percentage_html = format_html('<div class="text-muted text-end progress-percentage" style="font-size: 0.75rem; margin-top: 2px;">{completed}/{total} ({percentage_display}%)</div>', completed=completed_count, total=total_courses, percentage_display=formatted_percentage) # Added class 'progress-percentage'

    read_only_html = format_html('<div class="progress-display">{}</div>', mark_safe(progress_bar_html + percentage_html))

    # --- Part 2: Generate Editable Checkbox Form Inputs ---
    checkboxes_html = '<div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-2 mb-2">'
    for course in required_courses:
        checked_attr = 'checked' if course.id in completed_course_ids else ''
        checkbox_id = f'edit-course-{student.id}-{course.id}'
        checkboxes_html += format_html(
            '<div class="col">'
            '  <div class="form-check form-check-sm">'
            '    <input class="form-check-input progress-course-checkbox" type="checkbox" '
            '           name="completed_courses" value="{}" id="{}" {} '
            '           data-student-id="{}" data-course-id="{}" disabled>'
            '    <label class="form-check-label" for="{}">{}</label>'
            '  </div>'
            '</div>',
            course.id, checkbox_id, mark_safe(checked_attr),
            student.id, course.id,
            checkbox_id, course.code
        )
    checkboxes_html += '</div>'

    edit_form_html = format_html('<div class="progress-edit"><h6>Edit Completed Courses:</h6>{}</div>', mark_safe(checkboxes_html))

    final_html = read_only_html + edit_form_html
    return mark_safe(final_html)