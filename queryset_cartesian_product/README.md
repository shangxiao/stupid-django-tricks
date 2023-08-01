QuerySet Cartesian Products
===========================

July 2023


The definition of the [Cartesian product](https://en.wikipedia.org/wiki/Cartesian_product) is:

    Given 2 sets A, B, the Cartesian product is the set of all ordered pairs (a, b) where a is in A and b is in B.

This is denoted as A × B.

In SQL terms this is simply the result of [selecting from multiple tables, which is referred to as a "cross
join"](https://www.postgresql.org/docs/current/queries-table-expressions.html#QUERIES-FROM):

```sql
SELECT *
FROM A, B
```

which is roughly (see note in link) equivalent to explicitly declaring a [cross
join or inner join on true](https://www.postgresql.org/docs/15/queries-table-expressions.html#id-1.5.6.6.5.6.2):

```sql
SELECT *
FROM A CROSS JOIN B
```

```sql
SELECT *
FROM A INNER JOIN B ON TRUE
```


Implicit Joining in Django
--------------------------

Implicit joining is the process of taking the output of a Cartesian product and applying join predicates in the where
clause of the query.

This can currently be achieved with the `queryset.extra(tables=[...], where=[...])` method by supplying raw SQL.


Setting up a Cartesian Product & Implicit Joining on Querysets
--------------------------------------------------------------

Given that A × B can represent a Cartesian product, we can extend querysets to implement the `*` operator handling and
produce a new queryset that cross joins the operands as subqueries. This would allow us to define implicit joins like
so:

```python
class Shop(Model):
    objects = PatchedQuerySet.as_manager()  # Our new extended queryset
    name = CharField()


class Product(Model):
    name = CharField()
    shop = ForeignKey(Shop, ...)


shops = Shop.objects.all().values("id", "name")
products = Product.objects.all().values("id", "name", "shop_id")

cartesian_product = shops * products

implicit_join = cartesian_product.filter(shop_id=F("product_shop_id"))

print(list(implicit_join.filter(shop_name="KFC").values()))

# Outputs:

[
    {
        "id": 1,
        "shop_id": 1,
        "shop_name": "KFC",
        "product_name": "Original Recipe",
        "product_shop_id": 1,
    },
    {
        "id": 2,
        "shop_id": 1,
        "shop_name": "KFC",
        "product_name": "Hot n Spicy Wings",
        "product_shop_id": 1,
    },
]
```

The query produced is:

```sql
SELECT ROW_NUMBER() OVER () AS "id",
       (t.id) AS "shop_id",
       (t.name) AS "shop_name",
       (t2.name) AS "product_name",
       (t2.shop_id) AS "product_shop_id"
FROM
  (SELECT "queryset_cartesian_product_shop"."id",
          "queryset_cartesian_product_shop"."name"
   FROM "queryset_cartesian_product_shop") t,

  (SELECT "queryset_cartesian_product_product"."name",
          "queryset_cartesian_product_product"."shop_id"
   FROM "queryset_cartesian_product_product") t2
WHERE ((t.id) = (t2.shop_id)
       AND (t.name) = 'KFC')
```

The extended queryset could be implemented like this:


```python
class SubqueryJoin(Subquery):
    # just used to satisfy Query? eg existing_inner in build_filter()
    # but could still be useful?
    join_type = LOUTER
    table_name = "t"

class PatchedQuerySet(QuerySet):
    alias_name = "t"

    def __mul__(self, other):
        class AnonymousModel(models.Model):
            objects = PatchedQuerySet.as_manager()

        queryset = PatchedQuerySet(AnonymousModel)
        # explicitly set the required pk to just a row number
        # if doing a values() without fields id will still be added though
        queryset.query.default_cols = False
        queryset.query.add_annotation(Window(RowNumber()), "id")

        alias, _ = queryset.query.table_alias(self.alias_name, create=True)
        self_subquery = SubqueryJoin(self)
        self_subquery.template = f"{Subquery.template} {alias}"
        self_subquery.resolve_expression(query=queryset.query)
        queryset.query.alias_map[alias] = self_subquery

        for field in itertools.chain(
            self.query.values_select, self.query.annotations.keys()
        ):
            model_name = self.model._meta.model_name
            new_field_name = model_name + "_" + field
            queryset.query.add_annotation(
                RawSQL(sql=alias + "." + field, params=[]), new_field_name
            )

        other_alias, _ = queryset.query.table_alias(self.alias_name, create=True)
        other_subquery = SubqueryJoin(other)
        other_subquery.template = f", {Subquery.template} {other_alias}"
        other_subquery.resolve_expression(query=queryset.query)
        queryset.query.alias_map[other_alias] = other_subquery

        for field in itertools.chain(
            other.query.values_select, other.query.annotations.keys()
        ):
            new_field_name = other.model._meta.model_name + "_" + field
            queryset.query.add_annotation(
                RawSQL(sql=other_alias + "." + field, params=[]), new_field_name
            )

        return queryset
```


Notes
-----

 - A new queryset must be created, formed from the 2 querysets. This is easily done by making use of Django's Subquery.
 - Subquery is an expression, it implements `as_sql()` which is required by joins. Expressions also require having
   `resolve_expression()` called.
 - Each column in the new queryset needs to be prefixed/namespaced; for now I'm just using the subquery's model name but
   this would need to be improved to allow cartesian products of the same model.
 - Querysets require a model to function properly. Models are technically optional but not all queryset functionality is
   available. An annonymous unregistered model appears to work ok in this instance with initial basic testing.
 - The annonymous model will require _something_ for the primary key. In this case we can simply supply a row number.
 - If all the selected values from subqueries are added as annotations then filtering is automatically handled for us.
   This is easier if the subqueries have defined values. It's also possible to infer the columns to use in a similar
   manner to the way the compiler does.
