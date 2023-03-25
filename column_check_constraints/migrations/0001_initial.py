from django.db import migrations, models

import column_check_constraints.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "percentage",
                    column_check_constraints.models.CheckedIntegerField(
                        check=models.Q(("percentage__gte", 0), ("percentage__lte", 100))
                    ),
                ),
            ],
        ),
    ]
