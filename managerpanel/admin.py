# managerpanel/admin.py
from django.contrib import admin
from .models import ( # Import all models from this app
    CourseAssignment, ManagerProfile, FaceToFaceSession,
    Batch, Student, Cohort
)
# Import Semester and Year if needed for filtering/display
from responseupload.models import Semester, Year, Program, Course
from django.contrib.auth.models import User
from django import forms
from django.urls import reverse
from django.utils.html import format_html

# --- Cohort Admin ---
@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    """Admin interface for managing Cohorts."""
    list_display = ('name', 'description')
    search_fields = ('name',)

# --- Manager Profile Admin ---
@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    """Admin interface for managing Manager Profiles."""
    list_display = ('user_link', 'is_manager')
    list_filter = ('is_manager',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_select_related = ('user',)
    readonly_fields = ('user_link',)
    fields = ('user_link', 'is_manager')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            existing_manager_user_ids = ManagerProfile.objects.values_list('user_id', flat=True)
            kwargs["queryset"] = User.objects.exclude(
                id__in=existing_manager_user_ids
            ).exclude(
                is_superuser=True
            ).order_by('username')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description='User')
    def user_link(self, obj):
        link = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.username)

# --- Face-to-Face Session Inline ---
class FaceToFaceSessionInline(admin.TabularInline):
    """Inline admin for managing FaceToFace sessions within CourseAssignment."""
    model = FaceToFaceSession
    extra = 1
    fields = ('date', 'time', 'location', 'room_number', 'support_staff_name', 'it_support_name', 'it_support_number')
    ordering = ('date', 'time')

# --- Student Inline for Batch Admin ---
class StudentInline(admin.TabularInline):
    """Inline admin for viewing students within a Batch."""
    model = Student
    extra = 0
    fields = ('student_id_link', 'first_name', 'last_name', 'email', 'degree', 'status')
    readonly_fields = ('student_id_link', 'first_name', 'last_name', 'email', 'degree', 'status')
    can_delete = False
    show_change_link = False
    verbose_name = "Student in Batch"
    verbose_name_plural = "Students in Batch"
    ordering = ('last_name', 'first_name')

    @admin.display(description='Student ID')
    def student_id_link(self, obj):
        link = reverse("admin:managerpanel_student_change", args=[obj.id])
        return format_html('<a href="{}">{}</a>', link, obj.student_id)

# --- Batch Admin ---
@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    """Admin interface for managing Batches."""
    list_display = ('name', 'program', 'cohort', 'status', 'year', 'semester', 'student_count', 'created_at')
    list_filter = ('status', 'program', 'cohort', 'year', 'semester')
    search_fields = ('name', 'program__name', 'program__code', 'cohort__name')
    inlines = [StudentInline]
    list_select_related = ('semester', 'cohort', 'program')
    list_per_page = 20
    list_editable = ('status',)

    @admin.display(description='No. of Students', ordering='students__count')
    def student_count(self, obj):
        return obj.students.count()

# --- Student Admin (UPDATED with completed_courses) ---
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Admin interface for managing individual Students."""
    list_display = ('student_id', 'first_name', 'last_name', 'email', 'batch_link', 'degree', 'status', 'enrollment_semester')
    list_filter = ('status', 'degree', 'batch__status', 'batch__program', 'batch__cohort', 'batch', 'enrollment_semester')
    search_fields = ('student_id', 'first_name', 'last_name', 'email', 'batch__name', 'degree', 'batch__program__name', 'batch__program__code')
    list_select_related = ('batch', 'batch__cohort', 'batch__program', 'enrollment_semester')
    list_per_page = 25
    list_editable = ('status', 'degree')
    raw_id_fields = ('batch',)

    # Use filter_horizontal for completed_courses ManyToMany field
    filter_horizontal = ('completed_courses',)

    # Organize form fields using fieldsets
    fieldsets = (
        ('Personal Info', {
            'fields': ('student_id', 'first_name', 'last_name', 'email', 'phone_number')
        }),
        ('Academic Info', {
            'fields': ('batch', 'degree', 'enrollment_semester', 'status')
        }),
        ('Completed Courses', { # Section for the new field
            'classes': ('collapse',), # Optional: Make it collapsible by default
            'fields': ('completed_courses',)
        }),
         ('Other', {
            'fields': ('notes',)
        }),
    )

    @admin.display(description='Batch', ordering='batch__name')
    def batch_link(self, obj):
        if obj.batch:
            link = reverse("admin:managerpanel_batch_change", args=[obj.batch.id])
            # Include batch status in the link text
            return format_html('<a href="{}">{} [{}]</a>', link, obj.batch.name, obj.batch.get_status_display())
        return "-"

# --- Course Assignment Admin ---
@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for managing Course Assignments."""
    list_display = ('course', 'batch', 'semester', 'year', 'modality', 'get_meeting_days_display', 'start_date', 'get_faculty_members_display')
    list_filter = ('semester', 'year', 'modality', 'course__program', 'batch__status', 'batch', 'batch__cohort', 'faculty_members')
    search_fields = ('course__code', 'course__name', 'faculty_members__username', 'batch__name', 'batch__cohort__name', 'course__program__name', 'course__program__code')
    filter_horizontal = ('faculty_members',)
    inlines = [FaceToFaceSessionInline]
    date_hierarchy = 'start_date'
    raw_id_fields = ('course', 'batch', 'semester', 'year')
    list_select_related = ('course', 'batch', 'course__program', 'batch__cohort', 'semester', 'year')
    list_per_page = 20

    fieldsets = (
        (None, {
            'fields': ('course', 'batch', 'semester', 'year', 'modality', 'faculty_members')
        }),
        ('Schedule & Days', {
            'fields': ( ('start_date', 'end_date'), ('start_time', 'end_time'), ('meets_on_monday', 'meets_on_tuesday', 'meets_on_wednesday', 'meets_on_thursday'), ('meets_on_friday', 'meets_on_saturday', 'meets_on_sunday'), 'num_classes',),
        }),
        ('Online Details (Optional)', { 'classes': ('collapse',), 'fields': ('zoom_link', 'zoom_host_code'), }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Ensure related fields needed for filters/display are selected
        return qs.select_related(
            'course', 'batch', 'course__program', 'batch__cohort', 'semester', 'year'
            ).prefetch_related('faculty_members')

    @admin.display(description='Assigned Faculty')
    def get_faculty_members_display(self, obj):
        return ", ".join([f.get_full_name() or f.username for f in obj.faculty_members.all()])

    @admin.display(description='Meeting Days')
    def get_meeting_days_display(self, obj):
        return obj.get_meeting_days()