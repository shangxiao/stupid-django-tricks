ALL Subqueries
==============

An [ALL subquery](https://www.postgresql.org/docs/current/functions-subquery.html#FUNCTIONS-SUBQUERY-ALL)
is used to compare against subquery results and return true only if all rows satisfy the condition, false otherwise:


```
<operand> <operator> ALL (<subquery>)
```

The equivalent expression would be to use `NOT EXISTS` with an inverted subquery resultset:

```
NOT EXISTS (<inverted-subquery>)
```

where `<inverted-subquery>` inverts the `ALL` comparison logic, but not any correlating logic.

The `ALL` syntax may be preferrable to avoid double-negatives.


Example
-------

An example of where this can be useful is to filter a dataset where all rows of a uniquely-defined subset meet the same
condition.

Take the following trivial example where groups of employees are formed from differing restaurants:

```
# table groups;

                 name                  | employee |  restaurant
---------------------------------------+----------+--------------
 People from both KFC and Gami Chicken | Joe      | Gami Chicken
 People from both KFC and Gami Chicken | Bob      | KFC
 Only KFC                              | Bob      | KFC
 Only KFC                              | Alice    | KFC
(4 rows)
```

You can use an ALL subquery to get only groups where all members work for KFC:

```
# SELECT DISTINCT name
  FROM groups g
  WHERE 'KFC' = ALL (
    SELECT restaurant
    FROM groups g2
    WHERE g2.name = g.name
  );

   name
----------
 Only KFC
(1 row)
```

The equivalent `NOT EXISTS` expression would be:

```
# SELECT DISTINCT name
  FROM groups g
  WHERE NOT EXISTS (
    SELECT 1
    FROM groups g2
    WHERE g2.restaurant != 'KFC'
      AND g.name = g2.name
  );

   name
----------
 Only KFC
(1 row)
```


Database Support
----------------

 - ✗ SQLite: No support, use `NOT EXISTS` equivalent
 - ✓ [PostgreSQL](https://www.postgresql.org/docs/current/functions-subquery.html#FUNCTIONS-SUBQUERY-ALL)
 - ✓ [MySQL](https://dev.mysql.com/doc/refman/8.0/en/all-subqueries.html)
 - ✓ [SQL Server](https://docs.microsoft.com/en-us/sql/t-sql/language-elements/all-transact-sql)


Django
------

You achieve this in Django by defining a [custom lookup](https://docs.djangoproject.com/en/dev/howto/custom-lookups/)
that simply includes the `ALL` keyword along with the operator of choice. In fact any of the lookups using operators
that can be used in conjunction with ALL can be extended to do this:

```python
@Field.register_lookup
class All(Exact):
    lookup_name = "all"

    def get_rhs_op(self, connection, rhs):
        return connection.operators[super().lookup_name] % f"ALL {rhs}"
```

Then it can be used like so:

```python
class GroupsByRestaurant(Model):
    name = CharField(max_length=255)
    employee = CharField(max_length=255)
    restaurant = CharField(max_length=255)

subquery = GroupsByRestaurant.objects.filter(name=OuterRef("name")).values("restaurant")

only_groups_where_all_members_are_from_kfc = (
    GroupsByRestaurant.objects.annotate(only_kfc=Value("KFC"))
    .filter(only_kfc__all=Subquery(subquery))
    .values("name")
    .distinct()
)

print(only_groups_where_all_members_are_from_kfc.query)
```

Resulting query:

```
SELECT DISTINCT "all_subqueries_groupsbyrestaurant"."name"
FROM "all_subqueries_groupsbyrestaurant"
WHERE 'KFC' = ALL (
    SELECT U0."restaurant" FROM "all_subqueries_groupsbyrestaurant" U0
    WHERE U0."name" = ("all_subqueries_groupsbyrestaurant"."name")
)
```


Simplifying Filtering
---------------------

One can further refine the readability of the queryset filtering by creating a `Subquery` subclass similar
to `Exists` that can work with subqueries that create boolean results in the vein of Python's `all()` builtin:

```python
class All(Subquery):
    template = "'t' = ALL (%(subquery)s)"
    output_field = fields.BooleanField()

class Employee(Model):
    name = CharField()

class Score(Model):
    employee = ForeignKey(Employee)
    score = models.IntegerField()

Employee.objects.filter(
    All(
        Score.objects.filter(employee=OuterRef("id"))
        .annotate(score_gte_10=Q(score__gte=10))
        .values("score_gte_10")
    )
)
```

Resulting query:

```
SELECT "all_subqueries_employee"."id", "all_subqueries_employee"."name"
FROM "all_subqueries_employee"
WHERE 't' = ALL (
    SELECT (U0."score" >= 10) AS "score_gte_10"
    FROM "all_subqueries_score" U0
    WHERE U0."employee_id" = ("all_subqueries_employee"."id")
)
```


See [models.py](./models.py) and [tests.py](./tests.py) for more details.

