from datetime import date, datetime, timezone

from django.apps import AppConfig
from django.db.backends.postgresql.psycopg_any import get_adapters_template
from psycopg.types.datetime import (
    DateDumper,
    DateLoader,
    DatetimeDumper,
    TimestamptzLoader,
)


# Handling infinity is required if you want to use that for the valid time end placeholder
# ref: https://www.psycopg.org/psycopg3/docs/advanced/adapt.html#example-handling-infinity-date
class InfDateDumper(DateDumper):
    def dump(self, obj):
        if obj == date.max:
            return b"infinity"
        elif obj == date.min:
            return b"-infinity"
        else:
            return super().dump(obj)


class InfDateLoader(DateLoader):
    def load(self, data):
        breakpoint()
        if data == b"infinity":
            return date.max
        elif data == b"-infinity":
            return date.min
        else:
            return super().load(data)


class BaseTzLoader(TimestamptzLoader):
    """
    Load a PostgreSQL timestamptz using the a specific timezone.
    The timezone can be None too, in which case it will be chopped.
    """

    timezone = timezone.utc

    def load(self, data):
        res = super().load(data)
        return res.replace(tzinfo=self.timezone)


class InfTimestamptzLoader(BaseTzLoader):
    def load(self, data):
        if data == b"infinity":
            return datetime.max
        elif data == b"-infinity":
            return datetime.min
        else:
            return super().load(data)


class InfTimestamptzDumper(DatetimeDumper):
    def dump(self, obj):
        if obj == datetime.max:
            return b"infinity"
        elif obj == datetime.min:
            return b"-infinity"
        return super().dump(obj)


class BitemporalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bitemporal"

    def ready(self):
        ctx = get_adapters_template(True, timezone.utc)
        ctx.adapters.register_loader("timestamptz", InfTimestamptzLoader)
        ctx.adapters.register_dumper("datetime.datetime", InfTimestamptzDumper)
        # with connection.cursor() as cur:
        #     cur.connection.adapters.register_dumper(date, InfDateDumper)
        #     cur.connection.adapters.register_loader("date", InfDateLoader)
        #     cur.connection.adapters.register_dumper(datetime, InfDateDumper)
        #     cur.connection.adapters.register_loader("timestamptz", InfDateLoader)
        #     cur.connection.adapters.register_loader("timestamp", InfDateLoader)
