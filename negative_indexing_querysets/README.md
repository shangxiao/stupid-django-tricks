Negative Indexing QuerySets
===========================

February 2024


Django doesn't allow negative indexes on QuerySets, resulting in an exception if you try. Eg if you try to get the
last item of a queryset with the following you'll get:

```
Foo.objects.all()[-1]
  … traceback …
ValueError: Negative indexing is not supported.
```

So how does [`last()`](https://docs.djangoproject.com/en/stable/ref/models/querysets/#last) work?

The methods `first()` and `last()` force ordering on the queryset to produce deterministic results, if not already
ordered, [with `last()` behaving similarly to `first()` except with the ordering reversed](https://github.com/django/django/blob/ef2434f8508551fee183079ab471b1dc325c7acb/django/db/models/query.py#L1103).

Borrowing from `last()` we can extend `__getitem__()` to do the same thing for negative indexes then invert the index
(and subtract 1 to account for the 0 base):

```python
class OurQuerySet(QuerySet):
    def __getitem__(self, key):
        if isinstance(key, int) and key < 0:
            if self.ordered:
                queryset = self.reverse()
            else:
                self._check_ordering_first_last_queryset_aggregation(method="last")
                queryset = self.order_by("-pk")
            key = abs(key) - 1
            return queryset[key]
        else:
            return super().__getitem__(key)
```
