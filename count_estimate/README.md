Count Estimate
==============

August 2025


When dealing with large tables, you may start to notice that even simple counts of you data are running quite slowly.
Django views may require a count to proceed with operations, for eg in a `ListView` with pagination.

To help speed up places where the code does a count, but you don't necessarily want to remove the count from your code,
neither do you necessarily care about the _exact_ count - you may opt for an estimation instead.

In Postgres it's very cheap to get an estimation. It just requires that your stats are up to date:
https://wiki.postgresql.org/wiki/Count_estimate

There are 2 options:

 1. Getting the outright number of rows for a table using the `pg_class` table
 2. Examining the query plan's estimated number of resulting rows

The second option is quite easy with Django because it supports examining the query plan with `explain()`:

```python
>>> import json
>>> json.loads(Data.objects.all().explain(format="json"))[0]["Plan"]["Plan Rows"]
14329774
```

Notes:
 - You have to be sure that your stats are up to date. On a fresh table creation with no data the query planner returned
   2,040 rows. After running `ANALYZE` it then returned 1.
 - The more complex your query is the more the estimation errors compound. I've found the best results are with simple
   queries with simple filtering. On a more complex query with nesting the estimation was out by quite a big factor.
