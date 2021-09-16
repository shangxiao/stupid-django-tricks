Specifying a lookup expression on model properties
==================================================

Ever wanted to improve on the single point of control of properties by associating
additional attributes such as a lookup expresssion?

Given a model with this wild new property:

```python
class Foo(models.Model):
    foo = models.JSONField()

    @_property(lookup_expr="foo__bar")
    def bar(self):
        return self.foo["bar"]
```

You can now inspect the declared property attributes:

```python
> foo = Foo.objects.create(foo={"bar": "bar"})

> foo.bar
'bar'

> Foo.bar.lookup_expr
'foo__bar'
```

We no longer have to repeat the lookup expression throughout our code:

```python
class FooFilterSet(filters.FilterSet):
    bar = filters.CharFilter(lookup_expr=Foo.bar.lookup_expr)
```
