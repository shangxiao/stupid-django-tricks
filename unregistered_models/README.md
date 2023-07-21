Unregistered Models
===================

July 2023


If you have the need to write raw SQL for reporting you can use this trick to take advantage of the convenience of
`RawQuerySet` and having a model as the container:

```python
def series_report():
    class Series(Model):
        # A primary key is still necessary; either declare one or return a field
        # called 'id'
        generate_series = CharField(primary_key=True)

    Series.objects.raw("select generate_series(1, 10)")
```

Here `Series` is an model that isn't picked up by Django's registration process and thus doesn't participate in
migrations & checks.  It's useful for complex queries that can only be achieved with raw SQL where the result it a
trivial model with no complex fields like foreign keys that must be resolved during the registration process.

In fact Django will also add any extraneous columns as attributes to each model instance, meaning that the only field
that is required to be declared is the primary key:

```python
def test():
    class SimpleModel(Model):
        ...

    raw_queryset = SimpleModel.objects.raw("select 1 as id, 'Hello' as greeting")
    print(raw_queryset[0].id)
    print(raw_queryset[0].greeting)
```

The one thing you need to watch out for is declaring fields on the model that aren't selected as Django will attempt to
fetch these from the assumed backing table.
