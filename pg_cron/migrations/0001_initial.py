from django.contrib.postgres.operations import CreateExtension
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        # CreateExtension(name="pg_cron"),
        migrations.CreateModel(
            name="Job",
            fields=[
                ("jobid", models.BigIntegerField(primary_key=True, serialize=False)),
                ("schedule", models.TextField()),
                ("command", models.TextField()),
                ("nodename", models.TextField(db_default="localhost")),
                (
                    "nodeport",
                    models.IntegerField(
                        db_default=models.Func(function="inet_server_port")
                    ),
                ),
                (
                    "database",
                    models.TextField(
                        db_default=models.Func(function="current_database")
                    ),
                ),
                ("username", models.TextField()),
                ("active", models.BooleanField(db_default=True)),
                ("jobname", models.TextField()),
            ],
            options={
                "db_table": '"cron"."job"',
                "managed": False,
            },
        ),
    ]
