from django.db import migrations
from django.db import models

import pg_cron.models


class Migration(migrations.Migration):
    dependencies = [
        ("pg_cron", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MaterialisedView",
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
                ("source", models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="Source",
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
                ("source", models.IntegerField()),
            ],
            options={
                "constraints": [
                    pg_cron.models.ScheduleConstraint(
                        command="INSERT INTO pg_cron_source (source) values (1)",
                        name="insert_basic",
                        schedule="* * * * *",
                    )
                ],
            },
        ),
    ]
