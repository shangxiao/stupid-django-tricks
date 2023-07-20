from django.db import models
from django.db.models.expressions import Subquery
from django.db.models.sql.constants import LOUTER


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


class Post(models.Model):
    title = models.CharField()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField()
    email = models.CharField()
