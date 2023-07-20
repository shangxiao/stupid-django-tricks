Subqueries as Lateral Joins
===========================

July 2023


Scalar Subqueries in Django
---------------------------

[Django supports annotating & filtering](https://docs.djangoproject.com/en/4.2/ref/models/expressions/#subquery-expressions) expressions known as
[Scalar Subqueries](https://www.postgresql.org/docs/current/sql-expressions.html#SQL-SYNTAX-SCALAR-SUBQUERIES). These
allow you to fetch single-colum, single-row results into a query from another separate, possibly dependent, query.

The example in the Django docs is the following:

```python
newest = Comment.objects.filter(post=OuterRef("pk")).order_by("-created_at")
Post.objects.annotate(newest_commenter_email=Subquery(newest.values("email")[:1]))
```

And this produces a subquery in the `SELECT`:

```sql
SELECT "subqueries_as_lateral_joins_post"."id",
       "subqueries_as_lateral_joins_post"."title",
  (SELECT u0."email"
   FROM "subqueries_as_lateral_joins_comment" u0
   WHERE u0."post_id" = ("subqueries_as_lateral_joins_post"."id")
   ORDER BY u0."created_at" DESC
   LIMIT 1) AS "newest_commenter_email"
FROM "subqueries_as_lateral_joins_post"
```


Converting a Scalar Subquery into a Lateral Subquery
---------------------------------------------------

Subqueries can also be done in the `FROM` clause; If the subquery is correlated then you must define it as a [Lateral
Subquery](https://www.postgresql.org/docs/current/queries-table-expressions.html#QUERIES-LATERAL).

Using the lessons learned in Stupid Django Trick [Custom Joins](../custom_joins/README.md), we can use `query.join()` to
convert `Subquery` expressions annotated to a queryset into a lateral join:

```python
class SubqueryJoin:
    # required for Django
    filtered_relation = None
    nullable = False

    def __init__(self, *, query, table_alias, parent_alias, join_type=LOUTER):
        self.query = query
        self.table_alias = table_alias
        self.table_name = table_alias
        self.parent_alias = parent_alias
        self.join_type = join_type

    def as_sql(self, compiler, connection):
        query_sql, query_params = self.query.as_sql(compiler, connection)
        alias = connection.ops.quote_name(self.table_alias)
        return (
            f"{self.join_type} LATERAL {query_sql} {alias} ON ('t')",
            query_params,
        )

class JoinSubquery(Subquery):
    table_name = "subquery"

    def resolve_expression(self, query=None, **kwargs):
        resolved = super().resolve_expression(query, **kwargs)

        # Create an alias, will either be 'subquery' or a new Django created
        # U<N> alias this expression has already been used.
        resolved.alias, _ = resolved.query.table_alias(
            table_name=self.table_name, create=True
        )

        # Add our custom join here. We need the resolved query so as to resolve
        # any outer refs.
        subquery = SubqueryJoin(
            query=resolved.query,
            table_alias=resolved.alias,
            parent_alias=query.get_initial_alias(),
        )
        query.join(subquery)

        return resolved

    def as_sql(self, compiler, connection, template=None, **extra_context):
        alias = connection.ops.quote_name(self.alias)
        field_name = connection.ops.quote_name(self.query.values_select[0])
        # TODO: annotate multiple columns
        return f"{alias}.{field_name}", []
```

Updating the Django example above to use this subquery extension:

```python
newest = Comment.objects.filter(post=OuterRef("pk")).order_by("-created_at")
queryset = Post.objects.annotate(
    newest_commenter_email=JoinSubquery(newest.values("email")[:1])
)
```

will produce a lateral join like so:

```sql
SELECT "subqueries_as_lateral_joins_post"."id",
       "subqueries_as_lateral_joins_post"."title",
       "subquery"."email" AS "newest_commenter_email"
FROM "subqueries_as_lateral_joins_post"
INNER JOIN LATERAL
  (SELECT u0."email"
   FROM "subqueries_as_lateral_joins_comment" u0
   WHERE u0."post_id" = ("subqueries_as_lateral_joins_post"."id")
   ORDER BY u0."created_at" DESC
   LIMIT 1) "subquery" ON ('t')
```

These 2 versions of the query have very similar PostgreSQL query plans showing that the lateral join approach would
offer no real performance benefit.

The real benefit comes from the ability to select multiple columns & join on multiple rows – something which a scalar
subquery cannot provide. The challenge then becomes to get Django to annotate multiple columns.
