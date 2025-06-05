import django.contrib.postgres.fields.ranges
import django.db.models.constraints
import django.db.models.expressions
from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations, models

import abusing_constraints.constraints
import bitemporal.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        BtreeGistExtension(),
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "pk",
                    models.CompositePrimaryKey(
                        "name",
                        "valid_time",
                        blank=True,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField()),
                (
                    "valid_time",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(
                        db_default=django.db.models.expressions.RawSQL(
                            "tstzrange(now(), 'infinity', '[]')", params=[]
                        )
                    ),
                ),
                ("address", models.CharField()),
            ],
        ),
        migrations.CreateModel(
            name="Shift",
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
                ("account_name", models.CharField()),
                (
                    "valid_time",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                ("start_at", models.DateTimeField()),
                ("end_at", models.DateTimeField()),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=("account_name",), name="fuck"),
                    bitemporal.models.TemporalForeignKeyConstraint(
                        deferrable=django.db.models.constraints.Deferrable["DEFERRED"],
                        fields=("account_name", "valid_time"),
                        name="shift_account_temporal_fk",
                        to_fields=("name", "valid_time"),
                        to_model="bitemporal.account",
                    ),
                ],
            },
        ),
    ]
