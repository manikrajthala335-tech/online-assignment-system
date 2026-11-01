# Online Assignment Submission System — Django + MySQL

This is the integrated Django project for the Online Assignment Submission System.

## Technology
- Django
- MySQL
- HTML/CSS/JavaScript
- Django Templates
- File uploads

## ER diagram implemented
The database models follow the supplied ER diagram:
1. USER
2. TEACHER
3. SUBJECT
4. SUBJECT_REQUIREMENT
5. ENROLLMENT
6. ASSIGNMENT
7. SUBMISSION
8. GRADE
9. PRACTICAL_MARK
10. STUDENT_SUBJECT_MARK

Notifications are stored in the `Notification` model. The system creates them when a teacher posts an assignment, a student submits work, and a teacher records a grade.

## Setup on Windows

### 1. Create MySQL database
Open MySQL/phpMyAdmin and run:
CREATE DATABASE online_assignment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

### 2. Open PowerShell in this folder
Create a virtual environment:
python -m venv venv

Activate:
.\venv\Scripts\activate

If PowerShell blocks activation:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\activate

### 3. Install packages
pip install -r requirements.txt

### 4. Check MySQL settings
Open:
config/settings.py

Default configuration assumes:
NAME=online_assignment_db
USER=root
PASSWORD=
HOST=127.0.0.1
PORT=3306

Change these if your MySQL setup uses a different username/password/port. Do not place passwords in `settings.py`; set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` as environment variables instead.

Example for the current PowerShell session:
```powershell
$env:DB_NAME="online_assignment_db"
$env:DB_USER="root"
$env:DB_PASSWORD="your-mysql-password"
$env:DJANGO_SECRET_KEY="a-long-random-secret"
```

### 5. Create database tables
python manage.py makemigrations
python manage.py migrate

### 6. Create demo data
python manage.py seed_demo

Demo accounts:
Student: student@example.com / student123
Teacher: teacher@example.com / teacher123
Admin: admin@example.com / admin123

### 7. Start server
python manage.py runserver

Open:
http://127.0.0.1:8000/

## Useful URLs
Home:
http://127.0.0.1:8000/

Login:
http://127.0.0.1:8000/login/

Student:
http://127.0.0.1:8000/student/dashboard/

Teacher:
http://127.0.0.1:8000/teacher/dashboard/

Admin:
http://127.0.0.1:8000/admin-panel/dashboard/

Django built-in admin:
http://127.0.0.1:8000/django-admin/

## Testing flow

1. Login as teacher.
2. Open Subjects and create/check a subject.
3. Open Add Assignment and post an assignment.
4. Logout.
5. Login as student.
6. Open Subjects and ensure the student is enrolled.
7. Open Assignments.
8. Open the assignment and upload a PDF/DOC/DOCX/ZIP/TXT file.
9. Logout.
10. Login as teacher.
11. Open Submissions.
12. Review the submission and enter marks.
13. Open Grades.
14. Login as student again.
15. Check Grades and Subject Marks.

The project is now designed so that frontend pages are Django templates and forms are connected to Django views/models. MySQL stores the application data.

## Important
Before production use:
- Change SECRET_KEY.
- Set DEBUG=False.
- Configure ALLOWED_HOSTS.
- Configure a secure MySQL password.
- Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and `DJANGO_ALLOWED_HOSTS` as environment variables.
- Add production file/media storage.
