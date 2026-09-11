from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from core.models import User, Teacher, Subject, SubjectRequirement, Enrollment


class Command(BaseCommand):
    help = "Create demo users, teacher, subjects and enrollments."

    def handle(self, *args, **options):
        student, _ = User.objects.get_or_create(
            email="student@example.com",
            defaults={"name":"Student Demo","role":"student","password":make_password("student123")}
        )
        if not student.password.startswith("pbkdf2_"):
            student.password = make_password("student123"); student.save()

        teacher_user, _ = User.objects.get_or_create(
            email="teacher@example.com",
            defaults={"name":"Teacher Demo","role":"teacher","password":make_password("teacher123")}
        )
        teacher, _ = Teacher.objects.get_or_create(
            user=teacher_user,
            defaults={
                "employee_code":"EMP-001","qualification":"MSc CS",
                "department":"Computer Science","join_date":timezone.now().date()
            }
        )

        subjects = []
        for name, code in [("Database Management","DBMS-301"),("Web Technology","WT-302"),("Software Engineering","SE-303")]:
            s, _ = Subject.objects.get_or_create(
                subject_code=code,
                defaults={"subject_name":name,"teacher":teacher,"description":f"{name} subject"}
            )
            subjects.append(s)
            SubjectRequirement.objects.get_or_create(
                subject=s, defaults={"min_assignments":3,"description":"Minimum assignment requirement"}
            )
            Enrollment.objects.get_or_create(student=student, subject=s, defaults={"status":"active"})

        admin_user, _ = User.objects.get_or_create(
            email="admin@example.com",
            defaults={"name":"Admin Demo","role":"admin","password":make_password("admin123")}
        )
        if not admin_user.password.startswith("pbkdf2_"):
            admin_user.password = make_password("admin123"); admin_user.save()

        self.stdout.write(self.style.SUCCESS(
            "Demo data ready: student@example.com / student123, "
            "teacher@example.com / teacher123, admin@example.com / admin123"
        ))
