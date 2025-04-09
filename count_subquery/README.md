Count Subquery
==============

November 2024


Getting a count of a related model in Django is supported by way of simply aggregating on the related query name.

Given the following models:

```python
class Author(Model):
    name = CharField()

class Publication(Model):
    author = ForeignKey(Author, ...)
    title = CharField()
```

then you can get the count of publications like so using a join and group by:

```python
Author.objects.annotate(num_publications=models.Count('publication')).values('num_publications')
```

However if you have a complex query and you want to isolate the count then you may want to opt for a subquery. The
solution is not immediately obvious but you can use `Func("pk", function="COUNT")` to calculate the count of the
subquery.

Bundling this up into a convenient subclass of `Subquery` would simply be:

```python
class CountSubquery(Subquery):
    def __init__(self, queryset, **kwargs):
        super().__init__(
            queryset.values(_=Func("pk", function="COUNT")),
            **kwargs,
        )

Author.objects.annotate(num_publications=CountSubquery(Publication.objects.filter(author=OuterRef("pk"))))
```

If you wish to use `COUNT(*)` instead of the primary key then you can utilise Django's `Star()` expression:

```python
class CountSubquery(models.Subquery):
    def __init__(self, queryset, **kwargs):
        super().__init__(
            queryset.values(
                _=models.Func(
                    Star(), function="COUNT", output_field=models.IntegerField()
                )
            ),
            **kwargs,
        )
```
