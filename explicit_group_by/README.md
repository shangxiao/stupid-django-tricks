Explicit Group By
=================

April 2025


The way `GROUP BY` works with Django can be quite confusing for newcomers - because the intended development style is to
think about models & aggregation at a high level as opposed to thinking about the underlying SQL. The goal being to have a simpler
abstraction over SQL; but it comes at a cost of introducing more magic and creating code that's harder to comprehend as
we may find ourselves not understanding the queries it's producing underneath. This can be especially problematic when creating non-trivial queries.


There are a few behaviours that happen magically:
 - Querysets will [automatically flag](https://github.com/django/django/blob/5.2/django/db/models/query.py#L1692-L1698) that a `GROUP BY` must be constructed when an expression containing an aggregate is added via annotation or values
 - Django [allows influencing](https://github.com/django/django/blob/5.2/django/db/models/query.py#L1696-L1697) what fields or expressions can go into the `GROUP BY` via the values-before-annotate-aggregation pattern (arguable an anti-pattern due to the overloading of what `values()` is used for? perhaps not if you view `values()` as a way to select and returning
   dictionaires is just the appropriate container for that)
 - The compiler will compile a list of items for the `GROUP BY` from:
   - The influenced items
   - Any [additional items in the `SELECT` clause as determined by the final values](https://github.com/django/django/blob/5.2/django/db/models/sql/compiler.py#L137-L163)
   - Any [additional items in the `ORDER BY` clause as determined by `order_by()` **but excluding** `Meta.ordering`](https://github.com/django/django/blob/5.2/django/db/models/sql/compiler.py#L164-L169)
 - Django may try to [reduce `GROUP BY` expressions down to a functional equivalent by primary key](https://github.com/django/django/blob/5.2/django/db/models/sql/compiler.py#L198-L228),
   if supported by the database
 - Django may also try to [replace expressions with an ordinal reference to an expression declared in the `SELECT`](https://github.com/django/django/blob/5.2/django/db/models/sql/compiler.py#L185-L189), also
   if supported by the database

Note that any kind of aggregation requires a call to `values()` which returns the results as dictionaries.  This fits with the shape of the data returned where
each record does not correspond to a model instance.

Django does not yet understand that ...

The source of the confusion is ... (values overloaded - it does 3 things: sets up a dict iterator, sets the SELECT, inflences GROUP BY)


Legacy Behaviour
----------------

Here are some examples of how `GROUP BY` is constructed:

annotation of aggregate with `allows_group_by_selected_pks` turned off
```python
connection.features.allows_group_by_selected_pks = False
Product.objects.annotate(total=Count("*"))

> SELECT "explicit_group_by_product"."id",
         "explicit_group_by_product"."name",
         "explicit_group_by_product"."store_id",
         COUNT(*) AS "total"
  FROM "explicit_group_by_product"
  GROUP BY "explicit_group_by_product"."id",
           "explicit_group_by_product"."name",
           "explicit_group_by_product"."store_id"
```

annotation of aggregate with `allows_group_by_selected_pks` turned on
```python
connection.features.allows_group_by_selected_pks = True
Product.objects.annotate(total=Count("*"))

> SELECT "explicit_group_by_product"."id",
         "explicit_group_by_product"."name",
         "explicit_group_by_product"."store_id",
         COUNT(*) AS "total"
  FROM "explicit_group_by_product"
  GROUP BY "explicit_group_by_product"."id"
```

values-annotate with `allows_group_by_select_index` turned off
```python
connection.features.allows_group_by_select_index = False
Product.objects.values("name").annotate(total=Count("*"))

> SELECT "explicit_group_by_product"."name" AS "name",
         COUNT(*) AS "total"
  FROM "explicit_group_by_product"
  GROUP BY "explicit_group_by_product"."name"
```

values-annotate with `allows_group_by_select_index` turned on
```python
connection.features.allows_group_by_select_index = True
Product.objects.values("name").annotate(total=Count("*"))

> SELECT "explicit_group_by_product"."name" AS "name",
         COUNT(*) AS "total"
  FROM "explicit_group_by_product"
  GROUP BY 1
```

`order_by()` affecting the group by
```python
Product.objects.values("name").annotate(total=Count("*")).order_by("store")

> SELECT "explicit_group_by_product"."name" AS "name",
         COUNT(*) AS "total"
  FROM "explicit_group_by_product"
  GROUP BY "explicit_group_by_product"."name",
           "explicit_group_by_product"."store_id"
  ORDER BY "explicit_group_by_product"."store_id" ASC
```



Customising QuerySet, SQLCompiler for Explicit Grouping
-------------------------------------------------------

It's possible to setup an explicit group by mode like so:

```python
# legacy mode
Product.objects.values("name").annotate(total=Count("*")).order_by("-total")

# explicit group by mode
Product.objects.group_by("name").values("name", total=Count("*")).order_by("-total")
```

Here 


customise Django so that you can define an `group_by()` method on querysets, which enables an "explicit
grouping" mode to manually declare how you want `GROUP BY` to be defined, whilst also leave the legacy implicit grouping
behaviour to remain if `group_by()` is not used, for eg:


In order to do this the legacy behaviour would need to be bypassed if this new `group_by()` method is called:
 - The `Query.group_by` attribute will be one of either:
   - `None`: which tells the compiler to skip grouping
   - `True`: tells the compiler it needs to do grouping but it should just automatically infer the expressions to add
   - A tuple of expressions (<-CHECK): tells the compiler to add these in addition to the automatic inferencing
 - `Query.set_group_by()` sets the tuple of expressions as mentioned above. `True` values are set directly elsewhere in
   the code.
 - `SQLCompiler.get_group_by()`: the method called to construct the `GROUP BY` using `Query.group_by` as per above.

This means that a custom solution will need:
 1. A custom `QuerySet` that provides the `group_by()` interface
 2. A custom `Query` that the queryset uses during its initialisation.  It will need to:
   - Define its own attribute for storing requested group references & expressions
   - Bypass the default behaviour (necessary??) in `set_group_by()`
 3. A custom `SQLCompiler`. At this point in time there's no way to separate the grouping influencing behaviour from the
   automated inferencing behaviour in `get_group_by()` which means overriding the method and copying parts of the
   default implementation that helps with reference resolution & expression compilation, etc.


 - Sometimes it will include columns, sometimes not
 - having?
 - doesn't understand dependencies (unnecessary addition to group by when xxx functional(?) dependency)
 - Some of these depend on feature flags
 - It's unclear how it forms the group by clause, causing unnoticed bugs that can drastically affect the outcome
 - it's highly automated, varying and implicit

 - when there's an alias ie values(foo=) or annotate(foo=) then it does the ordinal crap


 - compiler.get_group_by()
   - gets everything in the select + order by and adds it to the group by regardless of functional dep


Order dependency
 - set_group_by() checks for query.values_select


values() can contain lookups or transforms, consider this when analysing set_group_by()


Approach to avoid Automation?
-----------------------------

 - Override and empty out `Query.set_group_by()`
 -


```
ipdb> self.select
(Col(explicit_group_by_product, explicit_group_by.Product.name),)
ipdb> self.values_select
('name',)
```


```
Product.objects.values('name').values('name', count=Count('*'))
SELECT "explicit_group_by_product"."name", COUNT(*) AS "count" FROM "explicit_group_by_product" GROUP BY "explicit_group_by_product"."name"

Product.objects.values('name').values(category=Coalesce('name', Value('Default value')), count=Count('*'))
SELECT COALESCE("explicit_group_by_product"."name", Default value) AS "category", COUNT(*) AS "count" FROM "explicit_group_by_product" GROUP BY "explicit_group_by_product"."name", 1

Product.objects.values(category=Coalesce('name', Value('Default value')), count=Count('*'))
SELECT COALESCE("explicit_group_by_product"."name", Default value) AS "category", COUNT(*) AS "count" FROM "explicit_group_by_product" GROUP BY "explicit_group_by_product"."id", 1
```



```
Product.objects.all().__dict__
{'model': explicit_group_by.models.Product,
 'alias_refcount': {},
 'alias_map': {},
 'alias_cols': True,
 'external_aliases': {},
 'table_map': {},
 'used_aliases': set(),
 'where': <WhereNode: (AND: )>,
 'annotations': {},
 'extra': {},
 '_filtered_relations': {}}


** group_by set to True

Product.objects.annotate(label=Concat(Value('Category: '), 'name'), count=Count('*')).query.__dict__
{'model': explicit_group_by.models.Product,
 'alias_refcount': {'explicit_group_by_product': 1},
 'alias_map': {'explicit_group_by_product': <django.db.models.sql.datastructures.BaseTable at 0x1061069c0>},
 'alias_cols': True,
 'external_aliases': {},
 'table_map': {'explicit_group_by_product': ['explicit_group_by_product']},
 'used_aliases': set(),
 'where': <WhereNode: (AND: )>,
 'annotations': {'label': Concat(ConcatPair(Value('Category: '), Col(explicit_group_by_product, explicit_group_by.Product.name))),
  'count': Count('*')},
 'extra': {},
 '_filtered_relations': {},
 '_annotation_select_cache': None,
 'filter_is_sticky': False,
 'group_by': True}


** group_by set to column

Product.objects.values('name').annotate(label=Concat(Value('Category: '), 'name'), count=Count('*')).query.__dict__
{'model': explicit_group_by.models.Product,
 'alias_refcount': {'explicit_group_by_product': 2},
 'alias_map': {'explicit_group_by_product': <django.db.models.sql.datastructures.BaseTable at 0x106110d10>},
 'alias_cols': True,
 'external_aliases': {},
 'table_map': {'explicit_group_by_product': ['explicit_group_by_product']},
 'used_aliases': set(),
 'where': <WhereNode: (AND: )>,
 'annotations': {'label': Concat(ConcatPair(Value('Category: '), Col(explicit_group_by_product, explicit_group_by.Product.name))),
  'count': Count('*')},
 'extra': {},
 '_filtered_relations': {},
 '_annotation_select_cache': {'label': Concat(ConcatPair(Value('Category: '), Col(explicit_group_by_product, explicit_group_by.Product.name))),
  'count': Count('*')},
 'filter_is_sticky': False,
 'select_related': False,
 'deferred_loading': (frozenset(), True),
 'select': (Col(explicit_group_by_product, explicit_group_by.Product.name),),
 'values_select': ('name',),
 'has_select_fields': True,
 'extra_select_mask': set(),
 '_extra_select_cache': None,
 'annotation_select_mask': ['label', 'count'],
 'default_cols': False,
 'base_table': 'explicit_group_by_product',
 'group_by': (Col(explicit_group_by_product, explicit_group_by.Product.name),
  Ref(label, Concat(ConcatPair(Value('Category: '), Col(explicit_group_by_product, explicit_group_by.Product.name)))))}

```
