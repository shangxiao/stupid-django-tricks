import django.db.models.deletion
from django.db import migrations, models

import xor_function.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Bar",
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
            name="Foo",
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
            name="User",
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
                ("is_standard_user_type", models.BooleanField(default=False)),
                ("is_staff_user_type", models.BooleanField(default=False)),
                ("is_admin_user_type", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Baz",
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
                    "bar",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="xor_function.bar",
                    ),
                ),
                (
                    "foo",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="xor_function.foo",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                check=xor_function.models.Xor(
                    models.F("is_standard_user_type"),
                    models.F("is_staff_user_type"),
                    models.F("is_admin_user_type"),
                ),
                name="only_one_type",
            ),
        ),
        migrations.AddConstraint(
            model_name="baz",
            constraint=models.CheckConstraint(
                check=xor_function.models.Xor(
                    models.Q(("foo", None), _negated=True),
                    models.Q(("bar", None), _negated=True),
                ),
                name="only_one_fk",
            ),
        ),
    ]
