Specific Ordering in SQL
========================

March 2025


Sometimes it's necessary to supply a specific ordering required for a model field defined by choices or categories.

There are a few ways to do this:

Case statements:

```sql
SELECT *
FROM orders
ORDER BY CASE WHEN status = 'IN_PROGRESS' THEN 1
              WHEN status = 'PAID' THEN 2
              WHEN status = 'SHIPPED' THEN 3
              WHEN status = 'DELIVERED' THEN 4
              ELSE 100
         END
```

Direct comparison, this is handy as you don't need to specify the ordering.  Note you need to specify `DESC` as you want
`true` results to have priority:

```sql
SELECT *
FROM orders
ORDER BY status = 'IN_PROGRESS' DESC,
         status = 'PAID' DESC,
         status = 'SHIPPED' DESC,
         status = 'DELIVERED' DESC
```

In PostgreSQL there's also the `array_position()` function which makes a nice concise `ORDER BY` clause:

```sql
SELECT *
FROM orders
ORDER BY array_position({'IN_PROGRESS', 'PAID', 'SHIPPED', 'DELIVERED'}, status)
```

Checkout the [tests](./tests.py) to see how this is done in Django.
