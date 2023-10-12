Overwriting Model Fields with Annotations
=========================================

October 2023


Using [annotate()](https://docs.djangoproject.com/en/4.2/ref/models/querysets/#annotate) to update a model's field is
forbidden in Django to prevent any accidental conflicts which might result in data loss:


```python
class Foo(Model):
    foo = IntegerField()

# Raises a ValueError with "The annotation 'foo' conflicts with a field on the model."
Foo.objects.annotate(foo=F('foo') + 1)
```

There are times, however, where it may be beneficial to define field filtering upon retrieval from the database without
having to define a new field, perhaps because code downstream doesn't know about any additional attributes. In these
circumstances your field is behaving similar in some ways to a "generated field".

If we bypass the conflict check in `annotate()` and go directly to the underlying mechanism in the `Query` object we
_can_ update model fields (note we can't chain these method calls, so we'll need a handle on the queryset):

```python
qs = Foo.objects.all()
qs.query.add_annotation(F('foo') + 1, 'foo')
qs.filter(...)
```
