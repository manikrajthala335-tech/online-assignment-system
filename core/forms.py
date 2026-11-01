from django import forms

from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.utils import timezone

import re

from .models import (
    Assignment,
    Enrollment,
    Grade,
    PracticalMark,
    StudentSubjectMark,
    Subject,
    SubjectRequirement,
    Submission,
    Teacher,
    User,
)


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        label="Password"
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "password",
            "password2",
            "role",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Normal users can register only as Student or Teacher.
        # Admin accounts cannot be created through public registration.
        self.fields["role"].choices = [
            ("student", "Student"),
            ("teacher", "Teacher"),
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        # Only allow Gmail addresses
        pattern = r"^[a-zA-Z0-9._%+-]+@gmail\.com$"

        if not re.match(pattern, email):
            raise ValidationError(
                "Please enter a valid Gmail address ending with @gmail.com."
            )

        return email

    def clean(self):
        cleaned = super().clean()

        # Check password confirmation
        if cleaned.get("password") != cleaned.get("password2"):
            raise ValidationError(
                "Passwords do not match."
            )

        # Extra backend protection:
        # Admin accounts cannot be created through registration.
        if cleaned.get("role") == "admin":
            raise ValidationError(
                "Admin accounts should be created by an administrator."
            )

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)

        user.password = make_password(
            self.cleaned_data["password"]
        )

        user.username = None

        if commit:
            user.save()

        return user


class LoginForm(AuthenticationForm):

    username = forms.EmailField(
        label="Email"
    )


class TeacherForm(forms.ModelForm):

    class Meta:
        model = Teacher
        fields = [
            "employee_code",
            "qualification",
            "department",
            "join_date",
        ]

        widgets = {
            "join_date": forms.DateInput(
                attrs={"type": "date"}
            )
        }


class SubjectForm(forms.ModelForm):

    class Meta:
        model = Subject
        fields = [
            "subject_name",
            "subject_code",
            "description",
            "has_practical",
        ]

        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 4}
            ),
            "has_practical": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),
        }


class SubjectRequirementForm(forms.ModelForm):

    class Meta:
        model = SubjectRequirement
        fields = [
            "min_assignments",
            "description",
        ]


class EnrollmentForm(forms.ModelForm):

    class Meta:
        model = Enrollment
        fields = [
            "subject"
        ]


class AssignmentForm(forms.ModelForm):

    class Meta:
        model = Assignment

        fields = [
            "subject",
            "title",
            "description",
            "instructions",
            "assignment_file",
            "deadline",
            "max_marks",
        ]

        widgets = {
            "deadline": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 4
                }
            ),

            "instructions": forms.Textarea(
                attrs={
                    "rows": 4
                }
            ),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data["deadline"]

        if deadline <= timezone.now():
            raise ValidationError(
                "Deadline must be in the future."
            )

        return deadline

    def clean_max_marks(self):
        max_marks = self.cleaned_data.get("max_marks")

        if max_marks is None:
            return max_marks

        if max_marks <= 0:
            raise ValidationError(
                "Maximum marks must be greater than 0."
            )

        return max_marks

    def clean_assignment_file(self):
        file = self.cleaned_data.get("assignment_file")

        if file:
            allowed = [
                ".pdf",
                ".doc",
                ".docx",
                ".zip",
                ".txt",
            ]

            filename = file.name.lower()

            if not any(
                filename.endswith(ext)
                for ext in allowed
            ):
                raise ValidationError(
                    "Allowed files: PDF, DOC, DOCX, ZIP, TXT."
                )

            if file.size > 10 * 1024 * 1024:
                raise ValidationError(
                    "Maximum file size is 10 MB."
                )

        return file


class SubmissionForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = [
            "file_path"
        ]

    def clean_file_path(self):
        f = self.cleaned_data["file_path"]

        allowed = {
            ".pdf",
            ".doc",
            ".docx",
            ".zip",
            ".txt",
        }

        name = f.name.lower()

        if not any(
            name.endswith(ext)
            for ext in allowed
        ):
            raise ValidationError(
                "Allowed files: PDF, DOC, DOCX, ZIP, TXT."
            )

        if f.size > 10 * 1024 * 1024:
            raise ValidationError(
                "Maximum file size is 10 MB."
            )

        return f


class GradeForm(forms.ModelForm):

    class Meta:
        model = Grade

        fields = [
            "total_marks",
            "feedback",
        ]

        widgets = {
            "total_marks": forms.NumberInput(
                attrs={
                    "min": 0
                }
            ),

            "feedback": forms.Textarea(
                attrs={
                    "rows": 4
                }
            ),
        }

    def __init__(
        self,
        *args,
        max_marks=None,
        **kwargs
    ):
        super().__init__(
            *args,
            **kwargs
        )

        self.max_marks = max_marks

        if max_marks is not None:
            self.fields[
                "total_marks"
            ].widget.attrs["max"] = max_marks

    def clean_total_marks(self):
        value = self.cleaned_data.get(
            "total_marks"
        )

        if value is None:
            return value

        if value < 0:
            raise ValidationError(
                "Marks cannot be negative."
            )

        if (
            self.max_marks is not None
            and value > self.max_marks
        ):
            raise ValidationError(
                f"Marks cannot exceed {self.max_marks}."
            )

        return value


class PracticalMarkForm(forms.ModelForm):

    class Meta:
        model = PracticalMark

        fields = [
            "criteria",
            "marks",
            "max_marks",
            "comments",
        ]

        widgets = {
            "marks": forms.NumberInput(
                attrs={
                    "min": 0
                }
            ),

            "max_marks": forms.NumberInput(
                attrs={
                    "min": 1
                }
            ),

            "comments": forms.Textarea(
                attrs={
                    "rows": 3
                }
            ),
        }

    def clean(self):
        cleaned = super().clean()

        marks = cleaned.get("marks")
        max_marks = cleaned.get("max_marks")

        # Maximum practical marks must be greater than zero.
        if (
            max_marks is not None
            and max_marks <= 0
        ):
            self.add_error(
                "max_marks",
                "Maximum marks must be greater than 0."
            )

        # Marks cannot be negative.
        if (
            marks is not None
            and marks < 0
        ):
            self.add_error(
                "marks",
                "Marks cannot be negative."
            )

        # Marks cannot exceed maximum marks.
        if (
            marks is not None
            and max_marks is not None
            and marks > max_marks
        ):
            self.add_error(
                "marks",
                f"Marks cannot exceed {max_marks}."
            )

        return cleaned


class UserEditForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            "name",
            "email",
        ]


class AdminUserEditForm(forms.ModelForm):

    class Meta:
        model = User

        # Role is intentionally not included.
        # Teacher users require a dedicated workflow/profile.
        fields = [
            "name",
            "email",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "is_active": forms.CheckboxInput(),
        }


class AdminSubjectForm(forms.ModelForm):

    class Meta:
        model = Subject

        fields = [
            "subject_name",
            "subject_code",
            "teacher",
            "description",
            "has_practical",
        ]

        widgets = {
            "subject_name": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "subject_code": forms.TextInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "teacher": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4
                }
            ),

            "has_practical": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input"
                }
            ),
        }