import abusing_constraints.constraints
import django.db.models.deletion
import xxx.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("start_timestamp", xxx.models.CalculatedField(output_field=models.DateTimeField())),
                ("end_timestamp", xxx.models.CalculatedField(output_field=models.DateTimeField())),
            ],
            options={
                "db_table": "event",
                "base_manager_name": "objects",
            },
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("location", models.CharField()),
                ("timezone", models.CharField()),
            ],
            options={
                "db_table": "location",
            },
        ),
        migrations.CreateModel(
            name="EventNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("note", models.CharField()),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="xxx.event")),
            ],
        ),
        migrations.AddField(
            model_name="event",
            name="location",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="xxx.location"),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=abusing_constraints.constraints.RawSQL(
                name="event_view",
                reverse_sql="DROP VIEW IF EXISTS event_view\n",
                sql="CREATE OR REPLACE VIEW event_view AS\nSELECT event.*,\n       timezone(location.timezone, (event.event_date + event.start_time)) AS start_timestamp,\n       timezone(location.timezone, (event.event_date + event.end_time)) AS end_timestamp\nFROM event\nINNER JOIN location ON location.id = event.location_id\n",
            ),
        ),
        migrations.AddConstraint(
            model_name="event",
            constraint=models.CheckConstraint(
                condition=models.Q(("start_time__lt", models.F("end_time"))), name="event_check"
            ),
        ),
    ]
