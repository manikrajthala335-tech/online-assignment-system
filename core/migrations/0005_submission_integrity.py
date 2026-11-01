from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0004_subject_has_practical")]

    operations = [
        migrations.AddConstraint(
            model_name="submission",
            constraint=models.UniqueConstraint(
                fields=("assignment", "student"),
                name="unique_student_assignment_submission",
            ),
        ),
    ]
