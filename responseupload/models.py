from django.db import models
from django.contrib.auth.models import User  # Import the default User model

# No need for Role or CustomUser models anymore

class Program(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class CourseSection(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Semester(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Year(models.Model):
    name = models.IntegerField(unique=True)

    def __str__(self):
        return str(self.name)

class Course(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.code} - {self.name} (Section: {self.section}, Sem: {self.semester}, Year: {self.year})"

class Faculty(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Use ForeignKey to User in FacultyResponse
class FacultyResponse(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)  # ForeignKey to User
    year = models.ForeignKey(Year, on_delete=models.CASCADE, blank=True, null=True)
    q1 = models.CharField(max_length=20, blank=True, null=True)
    q2 = models.CharField(max_length=20, blank=True, null=True)
    q3 = models.CharField(max_length=20, blank=True, null=True)
    q4 = models.CharField(max_length=20, blank=True, null=True)
    q5 = models.CharField(max_length=20, blank=True, null=True)
    q6 = models.CharField(max_length=20, blank=True, null=True)
    q7 = models.CharField(max_length=20, blank=True, null=True)
    q8 = models.CharField(max_length=20, blank=True, null=True)
    general_comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Faculty Response - {self.course}"

# Use ForeignKey to User in CourseResponse
class CourseResponse(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)  # ForeignKey to User
    year = models.ForeignKey(Year, on_delete=models.CASCADE, blank=True, null=True)
    q1 = models.CharField(max_length=20, blank=True, null=True)
    q2 = models.CharField(max_length=20, blank=True, null=True)
    q3 = models.CharField(max_length=20, blank=True, null=True)
    q4 = models.CharField(max_length=20, blank=True, null=True)
    general_comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Course Response - {self.course}"