from django.contrib import admin
from .models import (
    Assignment, Enrollment, Grade, PracticalMark, StudentSubjectMark,
    Subject, SubjectRequirement, Submission, Teacher, User
)

admin.site.register(User)
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(SubjectRequirement)
admin.site.register(Enrollment)
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(Grade)
admin.site.register(PracticalMark)
admin.site.register(StudentSubjectMark)
