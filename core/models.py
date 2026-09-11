from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("admin", "Admin"),
    ]

    id = models.BigAutoField(primary_key=True, db_column="user_id")
    username = None
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "role"]

    def __str__(self):
        return self.name or self.email


class Teacher(models.Model):
    teacher_id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True, related_name="teacher_profile")
    employee_code = models.CharField(max_length=50, unique=True)
    qualification = models.CharField(max_length=150)
    department = models.CharField(max_length=150)
    join_date = models.DateField()

    def __str__(self):
        return f"{self.employee_code} - {self.user.name}"


class Subject(models.Model):
    subject_id = models.BigAutoField(primary_key=True)
    subject_name = models.CharField(max_length=150)
    subject_code = models.CharField(max_length=50, unique=True)
    has_practical = models.BooleanField(default=False)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="subjects")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"


class SubjectRequirement(models.Model):
    requirement_id = models.BigAutoField(primary_key=True)
    subject = models.OneToOneField(Subject, on_delete=models.CASCADE, related_name="requirement")
    min_assignments = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Requirement for {self.subject.subject_name}"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    enrollment_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "subject"], name="unique_student_subject_enrollment")
        ]

    def __str__(self):
        return f"{self.student.name} - {self.subject.subject_name}"


class Assignment(models.Model):
    assignment_id = models.BigAutoField(primary_key=True)
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)

    assignment_file = models.FileField(
        upload_to="assignment_files/",
        blank=True,
        null=True
    )

    deadline = models.DateTimeField()
    max_marks = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def __str__(self):
        return self.title


class Submission(models.Model):
    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("graded", "Graded"),
    ]

    submission_id = models.BigAutoField(primary_key=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    file_path = models.FileField(upload_to="assignments/")
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")

    def __str__(self):
        return f"{self.student.name} - {self.assignment.title}"


class Grade(models.Model):
    grade_id = models.BigAutoField(primary_key=True)
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name="grade")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="grades")
    total_marks = models.PositiveIntegerField()
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.submission} - {self.total_marks}"


class PracticalMark(models.Model):
    practical_mark_id = models.BigAutoField(primary_key=True)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="practical_marks")
    criteria = models.CharField(max_length=150)
    marks = models.PositiveIntegerField()
    max_marks = models.PositiveIntegerField()
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"{self.criteria} - {self.marks}/{self.max_marks}"


class StudentSubjectMark(models.Model):
    student_subject_mark_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subject_marks")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="student_marks")
    total_obtained_marks = models.PositiveIntegerField(default=0)
    total_max_marks = models.PositiveIntegerField(default=0)
    grade_letter = models.CharField(max_length=5, blank=True)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "subject"], name="unique_student_subject_mark")
        ]

    def __str__(self):
        return f"{self.student.name} - {self.subject.subject_name}"
    
    
    
class Notification(models.Model):
    notification_id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.name} - {self.title}"   
    
    
     
    
