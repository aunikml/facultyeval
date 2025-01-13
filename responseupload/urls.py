from django.urls import path
from . import views

app_name = 'responseupload'

urlpatterns = [
    path('', views.home, name='home'),  # Add this line for the homepage
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('change_password/', views.change_password, name='change_password'),
    path('create_program/', views.create_program, name='create_program'),
    path('create_course/', views.create_course, name='create_course'),
    path('create_faculty/', views.create_faculty, name='create_faculty'),
    path('create_semester/', views.create_semester, name='create_semester'),
    path('create_year/', views.create_year, name='create_year'),
    path('create_course_section/', views.create_course_section, name='create_course_section'),
    path('faculty_responses/', views.view_faculty_responses, name='view_faculty_responses'),
    path('course_responses/', views.view_course_responses, name='view_course_responses'),
    path('course/<int:course_id>/faculty/<int:user_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/course/<int:user_id>/', views.course_response_detail, name='course_response_detail'),
]