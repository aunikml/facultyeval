from django import forms
from .models import FacultyResponse, CourseResponse, Program, Course, Faculty, CourseSection, Semester, Year
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'code']

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name', 'section', 'semester', 'year', 'program']

class CourseSectionForm(forms.ModelForm):
    class Meta:
        model = CourseSection
        fields = ['name']

class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['name']

class YearForm(forms.ModelForm):
    class Meta:
        model = Year
        fields = ['name']

class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ['first_name', 'last_name', 'email']
    
class CustomPasswordChangeForm(PasswordChangeForm):
    pass