@echo off
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Next steps:
echo 1. Create MySQL database: online_assignment_db
echo 2. Edit config\settings.py if your MySQL password is not blank.
echo 3. Run: python manage.py makemigrations
echo 4. Run: python manage.py migrate
echo 5. Run: python manage.py seed_demo
echo 6. Run: python manage.py runserver
pause
