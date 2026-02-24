from textwrap import dedent

from django.db import models
from django.db.models import CheckConstraint, F, Q, Value
from django.db.models.sql.datastructures import BaseTable

from abusing_constraints.constraints import RawSQL


class Location(models.Model):
    location = models.CharField()
    timezone = models.CharField()

    class Meta:
        db_table = "location"


create_event_view = """\
    CREATE OR REPLACE VIEW event_view AS
    SELECT event.*,
           timezone(location.timezone, (event.event_date + event.start_time)) AS start_timestamp,
           timezone(location.timezone, (event.event_date + event.end_time)) AS end_timestamp
    FROM event
    INNER JOIN location ON location.id = event.location_id
"""
drop_event_view = """\
    DROP VIEW IF EXISTS event_view
"""


class EventQuerySet(models.QuerySet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query.join(BaseTable("event_view", "event_view"))

    def update(self, *args, **kwargs):
        # xxx wrong
        # self.query.change_aliases({"event_view": "event"})
        self.query.alias_map["event_view"].table_name = "event"
        return super().update(*args, **kwargs)


class CalculatedField(models.Field):
    generated = True
    db_returning = False
    db_persist = False
    expression = Value(None)

    def __init__(self, *, output_field=None, **kwargs):
        self.output_field = output_field
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["output_field"] = self.output_field
        return name, path, args, kwargs

    def get_internal_type(self):
        return self.output_field.get_internal_type()

    def db_type(self, *args, **kwargs):
        # This prevents it from being migrated
        return None


class Event(models.Model):
    objects = EventQuerySet.as_manager()

    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    start_timestamp = CalculatedField(output_field=models.DateTimeField())
    end_timestamp = CalculatedField(output_field=models.DateTimeField())

    class Meta:
        base_manager_name = "objects"  # needed for refresh_from_db() / deferred attributes
        db_table = "event"
        constraints = [
            RawSQL(
                name="event_view",
                sql=dedent(create_event_view),
                reverse_sql=dedent(drop_event_view),
            ),
            # make sure that CalculatedField behaves nicely
            CheckConstraint(
                name="event_check",
                condition=Q(start_time__lt=F("end_time")),
            ),
        ]


class EventNote(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    note = models.CharField()
