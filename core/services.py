from django.db.models import Sum
from .models import Grade, PracticalMark, StudentSubjectMark


def calculate_subject_mark(student, subject):
    grades = Grade.objects.filter(
        submission__student=student,
        submission__assignment__subject=subject
    ).select_related("submission__assignment")

    assignment_obtained = sum(g.total_marks for g in grades)
    assignment_max = sum(
        g.submission.assignment.max_marks for g in grades
    )

    practical_marks = PracticalMark.objects.filter(
        grade__submission__student=student,
        grade__submission__assignment__subject=subject
    )

    practical_obtained = sum(m.marks for m in practical_marks)
    practical_max = sum(m.max_marks for m in practical_marks)

    obtained = assignment_obtained + practical_obtained
    max_marks = assignment_max + practical_max

    percentage = (
        (obtained / max_marks) * 100
        if max_marks
        else 0
    )

    if percentage >= 90:
        letter = "A+"
    elif percentage >= 80:
        letter = "A"
    elif percentage >= 70:
        letter = "B+"
    elif percentage >= 60:
        letter = "B"
    elif percentage >= 50:
        letter = "C+"
    elif percentage >= 40:
        letter = "C"
    else:
        letter = "F"

    mark, _ = StudentSubjectMark.objects.update_or_create(
        student=student,
        subject=subject,
        defaults={
            "total_obtained_marks": obtained,
            "total_max_marks": max_marks,
            "grade_letter": letter,
        },
    )

    return mark