import copy
import re
import textwrap

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


#
# A more generalised approach.
#
# Use this manager to simply read from a query attribute on the model
#


class VirtualTableManager(models.Manager):
    _query = None
    _params = {}

    class VirtualTable:
        join_type = None
        parent_alias = None
        filtered_relation = None

        def __init__(self, table_name, alias, query, params=None):
            self.table_name = table_name
            self.alias = alias
            self.query = query
            self.params = params

        def as_sql(self, compiler, connection):
            # Here's the magic: present the query as a sub-query where Django normally places the table name
            query = f"({self.query}) {self.alias}"

            if type(self.params) == dict:
                try:
                    # XXX mogrify dictionary params as Django only handles flat iterables
                    with connection.cursor() as cursor:
                        return cursor.mogrify(query, self.params).decode("utf-8"), []
                except KeyError:
                    # FIXME: Need to come up with a more robust solution
                    # If there's an issue mogrifying, then return some valid but empty sql
                    # This could happen if we do a Foo.objects.none(), where Django still tries to compile the sql
                    # but this will silently return nothing if we simply forgot to pass params when params are req'd
                    return "SELECT LIMIT 0", []
            else:
                return query, self.params

        def relabeled_clone(self, change_map):
            return self.__class__(
                self.table_name,
                change_map.get(self.table_alias, self.table_alias),
                self.query,
                self.params,
            )

    def get_queryset(self):
        qs = super().get_queryset()
        query = textwrap.dedent(self._query or self.model.query)
        qs.query.join(
            VirtualTableManager.VirtualTable(
                self.get_alias(), self.get_alias(), query, self._params
            )
        )
        return qs

    def get_alias(self):
        return re.sub(r"(?<!^)(?=[A-Z])", "_", self.model.__name__).lower()

    def query(self, query):
        # we only need a shallow copy?
        clone = copy.copy(self)
        clone._query = query
        return clone

    def params(self, **params):
        # we only need a shallow copy?
        clone = copy.copy(self)
        clone._params = params
        return clone


# Redefine GenerateIntegerSeries


class BetterGenerateIntegerSeries(models.Model):
    objects = VirtualTableManager()

    series = models.IntegerField(primary_key=True)

    query = "SELECT * FROM generate_series(%(start)s, %(stop)s, %(interval)s) series"

    class Meta:
        managed = False


def use_better_generate_integer_series():
    # use like so:
    BetterGenerateIntegerSeries.params(start=1, stop=10, interval=1).all()
