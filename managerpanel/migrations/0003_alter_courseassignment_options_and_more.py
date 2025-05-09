# Generated by Django 5.1.4 on 2025-04-21 20:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('managerpanel', '0002_managerprofile'),
        ('responseupload', '0005_remove_customuser_groups_remove_customuser_roles_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='courseassignment',
            options={'ordering': ['-start_date', 'course__code'], 'verbose_name': 'Course Assignment', 'verbose_name_plural': 'Course Assignments'},
        ),
        migrations.AlterModelOptions(
            name='managerprofile',
            options={'verbose_name': 'Manager Profile', 'verbose_name_plural': 'Manager Profiles'},
        ),
        migrations.AddField(
            model_name='courseassignment',
            name='modality',
            field=models.CharField(choices=[('online', 'Online'), ('f2f', 'Face-to-Face'), ('blended', 'Blended')], default='online', help_text='The primary delivery mode of the course (Online, Face-to-Face, Blended).', max_length=10),
        ),
        migrations.AddField(
            model_name='courseassignment',
            name='zoom_host_code',
            field=models.CharField(blank=True, help_text='Zoom host code (if applicable).', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='courseassignment',
            name='zoom_link',
            field=models.URLField(blank=True, help_text='Zoom meeting link for online sessions (if applicable).', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='courseassignment',
            name='course',
            field=models.ForeignKey(help_text='The specific course being assigned.', on_delete=django.db.models.deletion.CASCADE, to='responseupload.course'),
        ),
        migrations.AlterField(
            model_name='courseassignment',
            name='end_date',
            field=models.DateField(help_text='End date of the course assignment.'),
        ),
        migrations.AlterField(
            model_name='courseassignment',
            name='end_time',
            field=models.TimeField(help_text='Default end time for classes.'),
        ),
        migrations.AlterField(
            model_name='courseassignment',
            name='faculty_members',
            field=models.ManyToManyField(help_text='Faculty member(s) assigned to teach this course.', limit_choices_to={'is_staff': False, 'is_superuser': False}, related_name='assigned_courses', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='courseassignment',
            name='num_classes',
            field=models.IntegerField(blank=True, help_text='Optional: Total number of classes scheduled for this assignment.', null=True),
        ),
        migrations.AlterField(
            model_name='courseassignment',
            name='start_date',
            field=models.DateField(help_text='Start date of the course assignment.'),
        ),
        migrations.AlterField(
            model_name='courseassignment',
            name='start_time',
            field=models.TimeField(help_text='Default start time for classes.'),
        ),
        migrations.AlterField(
            model_name='managerprofile',
            name='is_manager',
            field=models.BooleanField(default=True, help_text='Designates whether this user has manager privileges.'),
        ),
        migrations.CreateModel(
            name='FaceToFaceSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(help_text='Date of the face-to-face session.')),
                ('time', models.TimeField(help_text='Time of the face-to-face session.')),
                ('location', models.CharField(help_text='Building or general location of the session.', max_length=200)),
                ('room_number', models.CharField(blank=True, help_text='Specific room number (optional).', max_length=50, null=True)),
                ('support_staff_name', models.CharField(blank=True, help_text='Name of the support staff member present (if any).', max_length=150, null=True)),
                ('it_support_name', models.CharField(blank=True, help_text='Name of the IT support contact (if any).', max_length=150, null=True)),
                ('it_support_number', models.CharField(blank=True, help_text='Contact number for IT support.', max_length=20, null=True)),
                ('course_assignment', models.ForeignKey(help_text='The course assignment this face-to-face session belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='f2f_sessions', to='managerpanel.courseassignment')),
            ],
            options={
                'verbose_name': 'Face-to-Face Session',
                'verbose_name_plural': 'Face-to-Face Sessions',
                'ordering': ['date', 'time'],
                'unique_together': {('course_assignment', 'date', 'time')},
            },
        ),
    ]
