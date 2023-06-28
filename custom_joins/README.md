Custom Joins
============

June 2023


Custom joins in Django are only officially supported with implicit joins through the use of the
[extra()](https://docs.djangoproject.com/en/4.2/ref/models/querysets/#extra) method.

Explicit joins can be achieved by using the undocumented & private query API:


```python
query = Query(SomeModel)
query.join(... your custom join here...)
```

The custom join should be something that's compatible with the `Join` class which is used by Django in a few places,
most notably when filters are added to a query to join to related models. For custom joining you're unlikely to want to
use `Join` itself as it's geared towards models & relationships between them.


Setting up a custom join defining `generate_series()`
-----------------------------------------------------

The PostgreSQL function `generate_series()` is useful for reporting over regular time periods where the data is stored
densely in order to correctly report 0s for the gaps where no data is present.

Something like this can be achieved by manually defining a join and adding it to the query which may be more desirable
than raw SQL as it's concise and reusable.


```python
class Data(Model):
    timestamp = DateTimeField()
    data = IntegerField()

series = GenerateSeries(
    start=datetime(2000, 1, 1, tzinfo=utc),
    stop=datetime(2000, 1, 5, tzinfo=utc),
    step=timedelta(days=1),
    join_condition=Q(
        timestamp__gte=SeriesRef(),
        timestamp__lte=SeriesRef() + Value(timedelta(days=1)),
    ),
)

dataset = (
    Data.objects.annotate(series)
    .values("series")
    .annotate(sum=Coalesce(Sum("data"), 0))
    .values("series", "sum")
    .order_by("series")
)
```

This produces a query & results like so:

```sql
stupid_django_tricks-#
SELECT "series" AS "series",
       coalesce(sum("custom_joins_data"."data"), 0) AS "sum"
FROM "custom_joins_data"
RIGHT OUTER JOIN generate_series('2000-01-01T00:00:00+00:00'::timestamptz, '2000-01-05T00:00:00+00:00'::timestamptz, '1 days 0.000000 seconds'::interval) "series"
  ON (("custom_joins_data"."timestamp" >= ("series") AND "custom_joins_data"."timestamp" <= ("series" + '1 days 0.000000 seconds'::interval)))
GROUP BY 1
ORDER BY 1 ASC;

         series         | sum
------------------------+-----
 2000-01-01 00:00:00+00 |   2
 2000-01-02 00:00:00+00 |   1
 2000-01-03 00:00:00+00 |   3
 2000-01-04 00:00:00+00 |   0
 2000-01-05 00:00:00+00 |   0
(5 rows)
```

Here's the definition of `GenerateSeries`.  A `SeriesRef` is required to allow use to refer to the series in the join
condition. `GenerateSeries` extends `SeriesRef` further to allow us to annotate it and hook into the expression
resolution process where it adds the necessary join to the query object.

```python
class SeriesRef(Ref):
    def __init__(self, alias=None, output_field=None):
        self.alias = alias
        self.output_field = output_field

    def as_sql(self, compiler, connection):
        return connection.ops.quote_name(self.alias), []

    def get_source_expressions(self):
        return []

    def get_refs(self):
        return {}

    def __repr__(self):
        # override Ref.__repr__ to avoid printing refs & source
        return "{}({})".format(self.__class__.__name__, self.alias)


class GenerateSeriesJoin:
    join_type = LOUTER  # required? does this keep join chaining outer?
    filtered_relation = None
    nullable = False

    def __init__(self, start, stop, step, join_clause, alias, parent_alias):
        self.start = start
        self.stop = stop
        self.step = step
        self.join_clause = join_clause
        self.table_name = alias
        self.table_alias = alias
        self.parent_alias = parent_alias

    def as_sql(self, compiler, connection):
        start, start_params = self.start.as_sql(compiler, connection)
        stop, stop_params = self.stop.as_sql(compiler, connection)
        params = [self.step]
        join_clause, join_params = self.join_clause.as_sql(compiler, connection)
        alias = connection.ops.quote_name(self.table_alias)
        return (
            f"RIGHT OUTER JOIN generate_series({start}, {stop}, %s) {alias} ON ({join_clause})",
            list(start_params) + list(stop_params) + params + join_params,
        )


class GenerateSeries(SeriesRef):
    """
    Overload SeriesRef so that we can additionally hook into expression resolution and setup our custom join.
    """

    def __init__(self, *, start, stop, step, join_condition, alias="series"):
        self.start = (
            models.Value(start) if not hasattr(start, "resolve_expression") else start
        )
        self.stop = (
            models.Value(stop) if not hasattr(stop, "resolve_expression") else stop
        )
        self.step = step
        self.join_condition = join_condition
        self.alias = alias
        # default_alias is what Django uses to determine the aggregations added to annotate()
        self.default_alias = alias

        self.output_field = self.start.output_field

        for expr in self.join_condition.flatten():
            if isinstance(expr, SeriesRef):
                expr.output_field = self.output_field
                expr.alias = self.alias

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        query.join(
            GenerateSeriesJoin(
                start=self.start.resolve_expression(query),
                stop=self.stop.resolve_expression(query),
                step=self.step,
                join_clause=self.join_condition.resolve_expression(query),
                alias=self.alias,
                parent_alias=query.get_initial_alias(),
            )
        )
        return self
```
