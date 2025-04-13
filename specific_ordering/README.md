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

Using the `array_position()` approach we can bundle that up into a neat little readable subclass of `OrderBy`:

```python
class ArrayPosition(Func):
    function = "array_position"
    output_field = IntegerField()

class OrderByValue(OrderBy):
    def __init__(self, field, order, *args, **kwargs):
        super().__init__(ArrayPosition(order, field), *args, **kwargs)

Order.objects.order_by(OrderByValue("status", ["IN_PROGRESS", "PAID", "SHIPPED", "DELIVERED"]))
```

Checkout the [tests](./tests.py) to see how this is done in Django.
