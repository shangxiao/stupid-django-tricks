import django.db.models.deletion
from django.db import migrations, models

import abusing_constraints.constraints


class Migration(migrations.Migration):
    dependencies = [
        ("abusing_constraints", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Child",
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
            ],
        ),
        migrations.CreateModel(
            name="Parent",
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
            ],
        ),
        migrations.AddField(
            model_name="child",
            name="parent",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="abusing_constraints.parent",
            ),
        ),
        migrations.AddConstraint(
            model_name="child",
            constraint=abusing_constraints.constraints.BasicForeignKeyConstraint(
                columns=["parent_id"],
                name="native_on_delete",
                on_delete="CASCADE",
                on_update=None,
                to_columns=["id"],
                to_table="abusing_constraints_parent",
            ),
        ),
    ]
