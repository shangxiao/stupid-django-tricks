from django.db import models


class GenerateSeriesVirtualTable:
    table_name = "series"
    table_alias = "series"
    join_type = None
    parent_alias = None
    filtered_relation = None

    def __init__(self, start, stop, interval):
        self.start = start
        self.stop = stop
        self.interval = interval

    def as_sql(self, compiler, connection):
        return "generate_series(%s, %s, %s) series", [
            self.start,
            self.stop,
            self.interval,
        ]


class GenerateSeriesManager(models.Manager):
    def all(self, start, stop, interval):
        self.start = start
        self.stop = stop
        self.interval = interval
        return super().all()

    def get_queryset(self):
        qs = super().get_queryset()
        qs.query.join(GenerateSeriesVirtualTable(self.start, self.stop, self.interval))
        return qs


class GenerateSeries(models.Model):
    objects = GenerateSeriesManager()

    class Meta:
        abstract = True
        managed = False


class GenerateIntegerSeries(GenerateSeries):
    series = models.IntegerField(primary_key=True)


# Although generate_series() will return sets of type timestamptz for both datetime and
# date arguments, PostgreSQL has a handy shortcut to access a different type through the
# `date`, `timestamp` and `timestamptz` fields of the returned set. If we wanted to be
# consistent and use `series` as the field name then we'd need to override models.DateField
# to convert the returned datetime to a date.


class GenerateDateSeries(GenerateSeries):
    date = models.DateField(primary_key=True)


class GenerateDateTimeSeries(GenerateSeries):
    timestamptz = models.DateTimeField(primary_key=True)
