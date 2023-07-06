ROLLUP Queries
==============

PostgreSQL, MySQL & Oracle offer the ability to extend the `GROUP BY` clause to aggregate on different combinations of
expressions in the group by known as "grouping sets". For example here is the [PostgreSQL
documentation](https://www.postgresql.org/docs/current/queries-table-expressions.html#QUERIES-GROUPING-SETS) showing how
these work along with the 2 shorthand notations `ROLLUP` and `CUBE`.

[Django doesn't support grouping sets](https://code.djangoproject.com/ticket/27646) and effecting the group by behaviour
is deceptively non-trivial due to the way it automatically determines the grouping based on what is being selected and
chosen for ordering.

To achieve this we need 2 things:


1 - Provide a way to wrap grouping fields with `ROLLUP ( ... )`
---------------------------------------------------------------

Here's an example of how to do this by forcing a query's `group_by` attribute to use a custom expression that manually
defines the `ROLLUP ( ... )`:

```python
class RollupGroupBy(Expression):
    output_field = models.BooleanField()

    def __init__(self, *fields):
        self.fields = fields

    def as_sql(self, compiler, connection):
        fields = ", ".join([connection.ops.quote_name(field) for field in self.fields])
        return [
            f"ROLLUP ({fields})",
            [],
        ]

class Rollup(Expression):
    output_field = models.BooleanField()

    def __init__(self, *fields):
        self.fields = fields

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        # XXX: override the attempt to group by all values
        # Note that we can't add any annotations to query here as this expression will be used with values() and the
        # mask will be in the process of being reset.
        query.group_by = [RollupGroupBy(*self.fields)]

        return self
```


2 - Stop fields selected with `values( ... )` and `order_by( ... )` from being added to the group by clause
-----------------------------------------------------------------------------------------------------------

It's not enough to simply define `ROLLUP` as we will need to select the grouped categrories as well as define an order
for deterministic results.  This can be done by crreating custom expressions that override `get_group_by_cols()` to
return empty lists:

```python
class RefNoGroup(Ref):
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

    def get_group_by_cols(self):
        return []

class OrderByNoGroup(OrderBy):
    def get_group_by_cols(self):
        return []
```


Usage
-----

The expressions above can then be used like so:

```python
(
    Data.objects.annotate(
        data_sum=Sum("data"),
    )
    .values(
        "data_sum",
        rollup=Rollup("category_1", "category_2"),
    )
    .values(
        "data_sum",
        cat_1=RefNoGroup("category_1", output_field=CharField()),
        cat_2=RefNoGroup("category_2", output_field=CharField()),
    )
    .order_by(
        OrderByNoGroup(F("category_1"), nulls_first=True),
        OrderByNoGroup(F("category_2"), nulls_first=True),
    )
)
```

which produces a query like so:

```sql
SELECT SUM("grouping_sets_data"."data") AS "data_sum",
       "category_1" AS "cat_1",
       "category_2" AS "cat_2"
FROM "grouping_sets_data"
GROUP BY ROLLUP ("category_1", "category_2")
ORDER BY "grouping_sets_data"."category_1" ASC NULLS FIRST,
         "grouping_sets_data"."category_2" ASC NULLS FIRST
```
