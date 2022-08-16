ALL Subqueries
==============

An [ALL subquery](https://www.postgresql.org/docs/current/functions-subquery.html#FUNCTIONS-SUBQUERY-ALL)
is used to compare against subquery results and return true only if all rows satisfy the condition, false otherwise.

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

You achieve this in Django by defining a [custom lookup](https://docs.djangoproject.com/en/dev/howto/custom-lookups/)
that simply includes the `ALL` keyword along with the operator of choice:

```python
@Field.register_lookup
class AllSubqueryLookup(Lookup):
    lookup_name = "all"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = list(lhs_params) + list(rhs_params)
        return "%s = ALL %s" % (lhs, rhs), params
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

See [models.py](./models.py) and [tests.py](./tests.py) for more details.
