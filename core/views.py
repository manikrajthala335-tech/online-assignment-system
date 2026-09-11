from django.contrib import messages
from django.http import HttpResponseForbidden,HttpResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .decorators import role_required
from .models import User
from .models import Teacher
from .forms import TeacherForm
from .forms import AdminUserEditForm
from .models import Notification


from .forms import (
    AssignmentForm,
    EnrollmentForm,
    GradeForm,
    LoginForm,
    PracticalMarkForm,
    RegisterForm,
    SubjectForm,
    AdminSubjectForm,
    SubjectRequirementForm,
    SubmissionForm,
    TeacherForm,
    UserEditForm
)

from .models import (
    Assignment, Enrollment, Grade, PracticalMark, StudentSubjectMark,
    Subject, SubjectRequirement, Submission, Teacher, User
)
from .services import calculate_subject_mark


def home(request):
    return render(request, "index.html")

def register_view(request):

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()

        if user.role == "teacher":
            Teacher.objects.create(
                user=user,
                employee_code=f"T{user.id:03d}",
                qualification="Not specified",
                department="Not specified",
                join_date=timezone.now().date()
            )

        messages.success(request, "Registration successful. Please log in.")
        return redirect("login")

    return render(request, "register.html", {"form": form})



def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    if request.user.role == "student":
        return redirect("student_dashboard")
    if request.user.role == "teacher":
        return redirect("teacher_dashboard")
    return redirect("admin_dashboard")


# ---------------- Student ----------------

@role_required("student")
def student_dashboard(request):
    subjects = Subject.objects.filter(enrollments__student=request.user, enrollments__status="active").distinct()
    assignments = Assignment.objects.filter(subject__in=subjects).order_by("deadline")
    submissions = Submission.objects.filter(student=request.user)
    grades = Grade.objects.filter(submission__student=request.user)
    avg = 0
    if grades:
        max_total = sum(g.submission.assignment.max_marks for g in grades)
        avg = round(sum(g.total_marks for g in grades) / max_total * 100, 1) if max_total else 0
    return render(request, "student/dashboard.html", {
        "subjects_count": subjects.count(),
        "assignments_count": assignments.filter(deadline__gte=timezone.now()).count(),
        "submissions_count": submissions.count(),
        "average": avg,
        "upcoming": assignments[:5],
        "recent_grades": grades.order_by("-graded_at")[:5],
    })


@role_required("student")
def student_subjects(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related("subject", "subject__teacher__user")
    return render(request, "student/subjects.html", {"enrollments": enrollments, "form": EnrollmentForm()})


@role_required("student")
def enroll_subject(request):
    if request.method != "POST":
        return redirect("student_subjects")
    form = EnrollmentForm(request.POST)
    if form.is_valid():
        enrollment = form.save(commit=False)
        enrollment.student = request.user
        enrollment.status = "active"
        try:
            enrollment.save()
            messages.success(request, "Subject enrolled successfully.")
        except Exception:
            messages.error(request, "You are already enrolled in this subject.")
    else:
        messages.error(request, "Please select a valid subject.")
    return redirect("student_subjects")


@role_required("student")
def student_assignments(request):
    subjects = Subject.objects.filter(enrollments__student=request.user, enrollments__status="active")
    assignments = Assignment.objects.filter(subject__in=subjects).select_related("subject").order_by("deadline")
    submission_map = {s.assignment_id: s for s in Submission.objects.filter(student=request.user, assignment__in=assignments)}
    return render(request, "student/assignments.html", {"assignments": assignments, "submission_map": submission_map})


@role_required("student")
def student_assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, assignment_id=assignment_id)
    enrolled = Enrollment.objects.filter(student=request.user, subject=assignment.subject, status="active").exists()
    if not enrolled:
        messages.error(request, "You are not enrolled in this subject.")
        return redirect("student_assignments")
    submission = Submission.objects.filter(student=request.user, assignment=assignment).order_by("-submitted_at").first()
    return render(request, "student/assignment_details.html", {
        "assignment": assignment, "submission": submission, "form": SubmissionForm()
    })


@role_required("student")
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, assignment_id=assignment_id)

    enrolled = Enrollment.objects.filter(
        student=request.user,
        subject=assignment.subject,
        status="active"
    ).exists()

    if not enrolled:
        messages.error(request, "You are not enrolled in this subject.")
        return redirect("student_assignments")

    if request.method != "POST":
        return redirect(
            "student_assignment_detail",
            assignment_id=assignment_id
        )

    if timezone.now() > assignment.deadline:
        messages.error(request, "The deadline has passed.")
        return redirect(
            "student_assignment_detail",
            assignment_id=assignment_id
        )

    form = SubmissionForm(request.POST, request.FILES)

    if form.is_valid():
        submission = form.save(commit=False)

        submission.assignment = assignment
        submission.student = request.user
        submission.is_late = timezone.now() > assignment.deadline
        submission.status = "submitted"

        submission.save()

        messages.success(
            request,
            "Assignment submitted successfully."
        )

        return redirect(
            "student_assignment_detail",
            assignment_id=assignment_id
        )

    # IMPORTANT: show validation errors
    return render(
        request,
        "student/assignment_details.html",
        {
            "assignment": assignment,
            "submission": None,
            "form": form,
        }
    )


@role_required("student")
def student_submissions(request):
    submissions = Submission.objects.filter(student=request.user).select_related("assignment", "assignment__subject").order_by("-submitted_at")
    return render(request, "student/submissions.html", {"submissions": submissions})


@role_required("student")
def student_grades(request):
    grades = Grade.objects.filter(submission__student=request.user).select_related(
        "submission__assignment__subject", "teacher__user"
    ).order_by("-graded_at")
    return render(request, "student/grades.html", {"grades": grades})


@role_required("student")
def student_subject_marks(request):
    subjects = Subject.objects.filter(enrollments__student=request.user)
    marks = []
    for subject in subjects:
        marks.append(calculate_subject_mark(request.user, subject))
    marks = StudentSubjectMark.objects.filter(student=request.user).select_related("subject")
    return render(request, "student/subject_marks.html", {"marks": marks})


@role_required("student")
def student_profile(request):
    form = UserEditForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("student_profile")
    return render(request, "student/profile.html", {"form": form})


@login_required
def student_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user
    )

    return render(
        request,
        "student/notifications.html",
        {
            "notifications": notifications
        }
    )


# ---------------- Teacher ----------------

@role_required("teacher")
def teacher_dashboard(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    subjects = teacher.subjects.all()
    assignments = Assignment.objects.filter(subject__in=subjects)
    pending = Submission.objects.filter(assignment__subject__in=subjects, status="submitted").count()
    return render(request, "teacher/dashboard.html", {
        "subjects_count": subjects.count(),
        "assignments_count": assignments.count(),
        "pending": pending,
        "graded": Grade.objects.filter(teacher=teacher).count(),
        "assignments": assignments.order_by("-created_at")[:5],
    })


@role_required("teacher")
def teacher_subjects(request):
    teacher = get_object_or_404(Teacher, user=request.user)

    subjects = teacher.subjects.all().order_by("subject_name")

    return render(
        request,
        "teacher/subjects.html",
        {
            "subjects": subjects
        }
    )
    
    
@role_required("teacher")
def teacher_assignments(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    assignments = Assignment.objects.filter(subject__teacher=teacher).select_related("subject").annotate(submission_count=Count("submissions"))
    return render(request, "teacher/assignments.html", {"assignments": assignments})


@role_required("teacher")
def add_assignment(request):
    teacher = get_object_or_404(Teacher, user=request.user)

    form = AssignmentForm(
        request.POST or None,
        request.FILES or None
    )

    # Only show subjects belonging to this teacher
    form.fields["subject"].queryset = Subject.objects.filter(
        teacher=teacher
    )

    if request.method == "POST" and form.is_valid():
        assignment = form.save(commit=False)

        # Security check
        if assignment.subject.teacher != teacher:
            messages.error(
                request,
                "You can only create assignments for your own subjects."
            )
            return redirect("add_assignment")

        assignment.save()

        messages.success(request, "Assignment posted successfully.")
        return redirect("teacher_assignments")

    return render(
        request,
        "teacher/add_assignment.html",
        {"form": form}
    )


@role_required("teacher")
def teacher_submissions(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    submissions = Submission.objects.filter(
        assignment__subject__teacher=teacher
    ).select_related("student", "assignment", "assignment__subject").order_by("-submitted_at")
    return render(request, "teacher/submissions.html", {"submissions": submissions})


@role_required("teacher")
def submission_details(request, submission_id):
    teacher = get_object_or_404(Teacher, user=request.user)
    submission = get_object_or_404(
        Submission.objects.select_related("student", "assignment", "assignment__subject"),
        submission_id=submission_id,
        assignment__subject__teacher=teacher
    )
    grade = Grade.objects.filter(submission=submission).first()
    form = GradeForm(request.POST or None, instance=grade, max_marks=submission.assignment.max_marks)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.submission = submission
        saved.teacher = teacher
        saved.save()
        submission.status = "graded"
        submission.save(update_fields=["status"])
        calculate_subject_mark(submission.student, submission.assignment.subject)
        messages.success(request, "Grade saved.")
        return redirect("teacher_submissions")
    return render(request, "teacher/submission_details.html", {"submission": submission, "form": form, "grade": grade})


@role_required("teacher")
def teacher_grades(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    grades = Grade.objects.filter(teacher=teacher).select_related("submission__student", "submission__assignment")
    return render(request, "teacher/grades.html", {"grades": grades})


@role_required("teacher")
def practical_marks(request, grade_id=None):
    teacher = get_object_or_404(Teacher, user=request.user)
    grade = None
    form = None
    if grade_id:
        grade = get_object_or_404(Grade, grade_id=grade_id, teacher=teacher)
        form = PracticalMarkForm(request.POST or None)
        if request.method == "POST" and form.is_valid(): 
            mark = form.save(commit=False)
            mark.grade = grade
            mark.save()

            calculate_subject_mark(
                grade.submission.student,
                grade.submission.assignment.subject
            )

            messages.success(request, "Practical mark saved.")
            return redirect("practical_marks_grade", grade_id=grade.grade_id)
    grades = Grade.objects.filter(teacher=teacher).select_related("submission__student", "submission__assignment")
    marks = PracticalMark.objects.filter(grade__teacher=teacher).select_related("grade")
    return render(request, "teacher/practical_marks.html", {"grades": grades, "grade": grade, "form": form, "marks": marks})


@role_required("teacher")
def teacher_profile(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    user_form = UserEditForm(request.POST or None, instance=request.user, prefix="user")
    teacher_form = TeacherForm(request.POST or None, instance=teacher, prefix="teacher")
    if request.method == "POST" and user_form.is_valid() and teacher_form.is_valid():
        user_form.save()
        teacher_form.save()
        messages.success(request, "Profile updated.")
        return redirect("teacher_profile")
    return render(request, "teacher/profile.html", {"user_form": user_form, "teacher_form": teacher_form, "teacher": teacher})


@login_required
@role_required("teacher")
def teacher_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user
    )

    return render(
        request,
        "teacher/notifications.html",
        {
            "notifications": notifications
        }
    )


# ---------------- Admin panel ----------------

@role_required("admin")
def admin_dashboard(request):
    return render(request, "admin_panel/dashboard.html", {
        "users": User.objects.count(),
        "teachers": Teacher.objects.count(),
        "subjects": Subject.objects.count(),
        "assignments": Assignment.objects.count(),
    })


@role_required("admin")
def admin_users(request):
    users = User.objects.all().order_by("-created_at")
    return render(request, "admin_panel/users.html", {"users": users})


@role_required("admin")
def admin_teachers(request):
    teachers = Teacher.objects.select_related("user").prefetch_related("subjects")
    return render(request, "admin_panel/teachers.html", {"teachers": teachers})


@role_required("admin")
def admin_edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, teacher_id=teacher_id)

    if request.method == "POST":
        form = TeacherForm(request.POST, instance=teacher)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Teacher information updated successfully."
            )

            return redirect("admin_teachers")

    else:
        form = TeacherForm(instance=teacher)

    return render(
        request,
        "admin_panel/edit_teacher.html",
        {
            "form": form,
            "teacher": teacher,
        }
    )


@role_required("admin")
def admin_delete_teacher(request, teacher_id):

    if request.method != "POST":
        return redirect("admin_teachers")

    teacher = get_object_or_404(
        Teacher.objects.select_related("user"),
        teacher_id=teacher_id
    )

    teacher_name = teacher.user.name
    teacher.user.delete()

    messages.success(
        request,
        f"Teacher {teacher_name} has been deleted successfully."
    )

    return redirect("admin_teachers")



@role_required("admin")
def admin_subjects(request):

    subjects = Subject.objects.select_related(
        "teacher__user"
    ).order_by("subject_name")

    form = AdminSubjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        subject = form.save()

        messages.success(
            request,
            f"Subject '{subject.subject_name}' has been assigned to "
            f"{subject.teacher.user.name}."
        )

        return redirect("admin_subjects")

    return render(
        request,
        "admin_panel/subjects.html",
        {
            "subjects": subjects,
            "form": form
        }
    )
    

@role_required("admin")
def admin_requirements(request):
    requirements = SubjectRequirement.objects.select_related("subject")
    form = SubjectRequirementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        subject_id = request.POST.get("subject")
        subject = get_object_or_404(Subject, subject_id=subject_id)
        req, _ = SubjectRequirement.objects.update_or_create(
            subject=subject,
            defaults=form.cleaned_data
        )
        messages.success(request, "Subject requirement saved.")
        return redirect("admin_requirements")
    return render(request, "admin_panel/requirements.html", {
        "requirements": requirements,
        "form": form,
        "subjects": Subject.objects.all(),
    })


@role_required("admin")
def admin_profile(request):
    form = UserEditForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("admin_profile")
    return render(request, "admin_panel/profile.html", {"form": form})


@role_required("admin")
def admin_notifications(request):
    return render(request, "admin_panel/notifications.html")


@login_required
def admin_delete_user(request, user_id):
    if request.user.role != "admin":
        return HttpResponseForbidden("You do not have permission to access this page.")

    if request.method == "POST":
        try:
            user = User.objects.get(id=user_id)

            # Prevent admin from deleting their own account
            if user.id == request.user.id:
                messages.error(request, "You cannot delete your own admin account.")
                return redirect("admin_users")

            user_name = user.name
            user.delete()

            messages.success(
                request,
                f"User {user_name} has been deleted successfully."
            )

        except User.DoesNotExist:
            messages.error(request, "User not found.")

    return redirect("admin_users")



@role_required("admin")
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Prevent admin from accidentally editing themselves
    if user == request.user:
        return redirect("admin_users")

    if request.method == "POST":
        form = AdminUserEditForm(request.POST, instance=user)

        if form.is_valid():
            form.save()
            return redirect("admin_users")

    else:
        form = AdminUserEditForm(instance=user)

    return render(
        request,
        "admin_panel/edit_user.html",
        {"form": form, "user_obj": user}
    )


@role_required("admin")
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Prevent admin from deleting themselves
    if user == request.user:
        return redirect("admin_users")

    if request.method == "POST":
        user.delete()
        return redirect("admin_users")

    return render(
        request,
        "admin_panel/delete_user.html",
        {"user_obj": user}
    )
    
@role_required("admin")
def admin_students(request):
    students = User.objects.filter(
        role="student"
    ).prefetch_related("enrollments").order_by("name")

    return render(
        request,
        "admin_panel/students.html",
        {
            "students": students
        }
    )    
    
    
    
@role_required("admin")
def admin_edit_student(request, user_id):
    student = get_object_or_404(
        User,
        id=user_id,
        role="student"
    )

    form = UserEditForm(
        request.POST or None,
        instance=student
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Student updated successfully."
        )

        return redirect("admin_students")

    return render(
        request,
        "admin_panel/edit_student.html",
        {
            "form": form,
            "student": student
        }
    )    
    
    
@role_required("admin")
def admin_delete_student(request, user_id):
    if request.method != "POST":
        return redirect("admin_students")

    student = get_object_or_404(
        User,
        id=user_id,
        role="student"
    )

    student_name = student.name
    student.delete()

    messages.success(
        request,
        f"Student '{student_name}' deleted successfully."
    )

    return redirect("admin_students")


@role_required("admin")
def admin_reports(request):

    # -----------------------------
    # Basic totals
    # -----------------------------

    total_students = User.objects.filter(
        role="student"
    ).count()

    total_teachers = Teacher.objects.count()

    total_subjects = Subject.objects.count()

    total_assignments = Assignment.objects.count()


    # -----------------------------
    # Student status
    # -----------------------------

    active_students = User.objects.filter(
        role="student",
        is_active=True
    ).count()

    inactive_students = User.objects.filter(
        role="student",
        is_active=False
    ).count()


    student_status_data = {
        "labels": [
            "Active",
            "Inactive"
        ],
        "data": [
            active_students,
            inactive_students
        ]
    }


    # -----------------------------
    # Submission status
    # -----------------------------

    submitted_count = Submission.objects.filter(
        status="submitted"
    ).count()

    graded_count = Submission.objects.filter(
        status="graded"
    ).count()


    submission_status_data = {
        "labels": [
            "Submitted",
            "Graded"
        ],
        "data": [
            submitted_count,
            graded_count
        ]
    }


    # -----------------------------
    # Assignments per teacher
    # -----------------------------

    teachers = Teacher.objects.select_related(
        "user"
    ).annotate(
        assignment_count=Count(
            "subjects__assignments"
        )
    ).order_by("user__name")


    teacher_assignment_data = {
        "labels": [
            teacher.user.name
            for teacher in teachers
        ],

        "data": [
            teacher.assignment_count
            for teacher in teachers
        ]
    }


    # -----------------------------
    # Students per subject
    # -----------------------------

    subjects = Subject.objects.annotate(
        student_count=Count("enrollments")
    ).order_by("subject_name")


    subject_enrollment_data = {
        "labels": [
            subject.subject_code
            for subject in subjects
        ],

        "data": [
            subject.student_count
            for subject in subjects
        ]
    }


    return render(
        request,
        "admin_panel/reports.html",
        {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_subjects": total_subjects,
            "total_assignments": total_assignments,

            "student_status_data": student_status_data,

            "submission_status_data": submission_status_data,

            "teacher_assignment_data": teacher_assignment_data,

            "subject_enrollment_data": subject_enrollment_data,
        }
    )
