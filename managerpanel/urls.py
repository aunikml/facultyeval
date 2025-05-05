# managerpanel/urls.py
from django.urls import path
from . import views

app_name = 'managerpanel'

urlpatterns = [
    path('dashboard/', views.manager_dashboard, name='manager_dashboard'),
    # --- Assignment URLs ---
    path('assignments/', views.list_course_assignments, name='list_assignments'),
    path('assign/', views.create_course_assignment, name='create_course_assignment'),
    path('edit/<int:assignment_id>/', views.edit_course_assignment, name='edit_course_assignment'),
    path('delete/<int:assignment_id>/', views.delete_course_assignment, name='delete_course_assignment'),
    # --- Component Creation URLs ---
    path('create/program/', views.create_program_manager, name='create_program_manager'),
    path('create/semester/', views.create_semester_manager, name='create_semester_manager'),
    path('create/year/', views.create_year_manager, name='create_year_manager'),
    path('create/course/', views.create_course_manager, name='create_course_manager'),
    # --- Batch Management URLs ---
    path('batches/', views.list_batches, name='list_batches'),
    path('batches/create/', views.create_batch, name='create_batch'),
    path('batches/edit/<int:batch_id>/', views.edit_batch, name='edit_batch'),
    path('batches/delete/<int:batch_id>/', views.delete_batch, name='delete_batch'),
    path('batches/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('batches/update_status/<int:batch_id>/', views.update_batch_status, name='update_batch_status'),
    # --- Student Management URLs ---
    path('students/search/', views.search_students, name='search_students'),
    path('batches/<int:batch_id>/add_student/', views.add_student_manual, name='add_student_manual'),
    path('students/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('students/upload/', views.upload_students_csv, name='upload_students_csv'),

    # --- THIS IS THE CORRECT URL for single course status update ---
    path('students/update_course_status/<int:student_id>/', views.update_single_course_status, name='update_single_course_status'),

    # --- MAKE SURE THE LINE BELOW IS DELETED OR COMMENTED OUT ---
    # path('students/update_progress/<int:student_id>/', views.update_student_progress, name='update_student_progress'), # <-- DELETE THIS LINE

]