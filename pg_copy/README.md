Fast CSV Exports with COPY
==========================

August 2025

If you're using Postgres and you require fast & efficient CSV exports of your data then you may wish to take a look at
using the `COPY` command.

Both `psycopg2` and `psycopg` (3) support `COPY`.

Some caveats:

 - Since `COPY` is intended for exporting & importing, it must distinguish between `NULL` and empty string. It does this
   by exporting `NULL` values as unquoted empty strings while empty strings are exported as quoted empty strings. There
   is no way to affect this behaviour. It isn't really important unless you're directly examining or comparing the raw
   CSV.
 - The way to specify readable labels in the header is to use a query and to alias your columns. Django QuerySets don't
   support setting aliases with invalid characters, like whitespace, so that it can set appropriately named object
   attributes. If you want to use QuerySets then you must override the behaviour that enforces this.
 - You can "mogrify" a queryset to get the underlying SQL to be used with `COPY` but you must also account for when
   `EmptyResultSet` is raised.  See [views.py](./views.py) for implementation details.
 - The tradeoff here is abstraction: we aren't explicitly defining the CSV columns and so data may be exposed without us
   knowing. Django likes to add columns to queryset queries, take care to test and assert what is being exported so as not to
   accidentally leak data.

Additionally you need to start thinking about formatting of your data in the database. Here are some things that you'll
typically need to consider that are normally done in Python & Django quite easily:

 - If you need any timestamps in a local timezone then you'll need to deal with that: Either set the time zone of the
   session using `SET TIME ZONE` or for each column with the `AT TIME ZONE` clause.
 - Formatting of timestamps using the `to_char()` function.
 - Getting the `choices` display value.
 - Converting booleans to something more readable.


```python
def export(request):
    queryset = Product.objects.filter(...).values(
        **{
            'Label with spaces': F('field'),
            # define AtTimeZone and ToChar as subclasses of Func
            'A timestamp': ToChar(AtTimeZone('timestamp', timezone='Hongkong'), Value('format-string')),
        }
    # Remember to refer to the alias defined above, if you refer to a column it will get included in the export
    ).order_by(...)

    # Optionally set the timezone for the session
    # cursor.execute("SET TIME ZONE 'Hongkong'")

    with connection.cursor() as cursor:
        with cursor.copy(
            "COPY ({}) TO STDOUT WITH (FORMAT csv, HEADER)".format(
                mogrify_queryset(queryset)
            )
        ) as copy:
            return HttpResponse(
                copy,
                headers={"Content-Disposition": 'attachment; filename="export.csv"'},
            )
```
