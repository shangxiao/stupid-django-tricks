from django.db import models
from django.db.models.constraints import BaseConstraint
from django.db.models.expressions import Func


class Schedule(Func):
    function = "cron.schedule"


class Unschedule(Func):
    function = "cron.unschedule"


class ScheduleConstraint(BaseConstraint):
    def __init__(self, *args, schedule, command, **kwargs):
        super().__init__(*args, **kwargs)
        self.schedule = schedule
        self.command = command

    def create_sql(self, model, schema_editor):
        if hasattr(self.command, "resolve_expression"):
            # ...
            pass
        else:
            command = self.command

        # just always specify job_name, reuse name
        return f"SELECT cron.schedule('{self.name}', '{self.schedule}', '{command}')"

    def remove_sql(self, model, schema_editor):
        return f"SELECT cron.unschedule('{self.name}')"

    def constraint_sql(self, model, schema_editor):
        return None

    def validate(self, *args, **kwargs):
        return True

    def __eq__(self, other):
        if isinstance(other, ScheduleConstraint):
            return self.name == other.name
        return super().__eq__(other)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["schedule"] = self.schedule
        kwargs["command"] = self.command
        return path, args, kwargs


class Job(models.Model):
    jobid = models.BigIntegerField(primary_key=True)
    schedule = models.TextField()
    command = models.TextField()
    nodename = models.TextField(db_default="localhost")
    nodeport = models.IntegerField(
        db_default=Func(function="inet_server_port")
    )  # this can return null
    database = models.TextField(db_default=Func(function="current_database"))
    username = models.TextField()  # default CURRENT_USER
    active = models.BooleanField(db_default=True)
    jobname = models.TextField()

    class Meta:
        db_table = '"cron"."job"'
        managed = False

    def __str__(self):
        return self.jobname

    def __repr__(self):
        return f"<Job: {self.jobname} - {self.schedule}>"


class Source(models.Model):
    source = models.IntegerField()

    class Meta:
        constraints = [
            ScheduleConstraint(
                name="insert_basic",
                schedule="* * * * *",
                command="INSERT INTO pg_cron_source (source) values (1)",
            ),
        ]

    def __str__(self):
        return str(self.source)


class MaterialisedView(models.Model):
    source = models.IntegerField()

    class Meta:
        constraints = []

    def __str__(self):
        return str(self.source)
